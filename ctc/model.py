from paddle import v2 as paddle
from paddle.v2 import layer
from paddle.v2.activation import Relu, Linear
from paddle.v2.networks import img_conv_group, simple_gru


def ocr_convs(input_image, num, with_bn):
    '''
    @input_image: input image
    '''
    assert num % 4 == 0

    tmp = img_conv_group(
        input=input_image,
        num_channels=1,
        conv_padding=1,
        conv_num_filter=[16] * (num / 4),
        conv_filter_size=3,
        conv_act=Relu(),
        conv_with_batchnorm=with_bn,
        pool_size=2,
        pool_stride=2, )

    tmp = img_conv_group(
        input=tmp,
        conv_padding=1,
        conv_num_filter=[32] * (num / 4),
        conv_filter_size=3,
        conv_act=Relu(),
        conv_with_batchnorm=with_bn,
        pool_size=2,
        pool_stride=2, )

    tmp = img_conv_group(
        input=tmp,
        conv_padding=1,
        conv_num_filter=[64] * (num / 4),
        conv_filter_size=3,
        conv_act=Relu(),
        conv_with_batchnorm=with_bn,
        pool_size=2,
        pool_stride=2, )

    tmp = img_conv_group(
        input=tmp,
        conv_padding=1,
        conv_num_filter=[128] * (num / 4),
        conv_filter_size=3,
        conv_act=Relu(),
        conv_with_batchnorm=with_bn,
        pool_size=2,
        pool_stride=2, )

    return tmp


class Model(object):
    def __init__(self, num_classes, shape):
        self.num_classes = num_classes
        self.shape = shape
        self.image_vector_size = shape[0] * shape[1]

        self.__declare_input_layers__()
        self.__build_nn__()

    def __declare_input_layers__(self):
        self.image = layer.data(
            name='image',
            type=paddle.data_type.dense_vector(self.image_vector_size),
            height=self.shape[0],
            width=self.shape[1])

        self.label = layer.data(
            name='label',
            type=paddle.data_type.integer_value_sequence(self.num_classes))

    def __build_nn__(self):
        conv_features = ocr_convs(self.image, 8, True)

        sliced_feature = layer.block_expand(
            input=conv_features,
            num_channels=128,
            stride_x=1,
            stride_y=1,
            block_x=1,
            block_y=11)

        gru_forward = simple_gru(input=sliced_feature, size=128, act=Relu())
        gru_backward = simple_gru(
            input=sliced_feature, size=128, act=Relu(), reverse=True)

        self.output = layer.fc(
            input=[gru_forward, gru_backward],
            size=self.num_classes + 1,
            act=Linear())

        self.cost = layer.warp_ctc(
            input=self.output,
            label=self.label,
            size=self.num_classes + 1,
            norm_by_times=True,
            blank=self.num_classes)
