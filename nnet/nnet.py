# encoding: utf-8
import ee

# Neural Network DEFINITION
class Neuron:
    def __init__(self, weights, bias):
        """
        :param weights: List of neuron's weights 
        :param bias: Bias
        """
        self.weights = weights
        self.bias = bias

    # TODO: check shape of inputs and weights
    def out(self, inputs):
        """Return neuron output
        
        :param inputs: List of EE images
        :return: EE image 
        """
        # self.check()

        w0 = ee.Image(self.weights)
        potential = inputs.multiply(w0)
        potential = potential.reduce(ee.Reducer.sum())
        potential = potential.add(ee.Image(self.bias))
        # TODO: create sigmoid function
        output = potential.expression(
            '1.0 / (1 + exp(-potential))',
            {'potential': potential.select('sum')}
        )

        return(output)


class Layer:
    def __init__(self, neuron_list):
        self.neurons = neuron_list

    def outs(self, inputs):
        outs = []
        for n in self.neurons:
            outs.append(n.out(inputs))

        return ee.Image.cat(outs)


class NNet:
    def __init__(self, layers):
        """Create NNet
        
        :param layers: list of layers 
                       layers[0] is first hidden layer, 
                       layers[-1] is the output layer
        """
        self.layers = layers

    def outs(self, inputs):
        layer_out = inputs
        for lr in self.layers:
            layer_out = lr.outs(layer_out)

        return layer_out



