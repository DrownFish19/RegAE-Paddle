"""
输入数据类型 10^5 * 100 * 100

1.按照8：2划分训练数据集和测试数据集
2.通过训练数据进行标准正则化
"""
import numpy as np
import paddle
from paddle.io import Dataset, DataLoader


class ScalerStd(object):
    """
    Desc: Normalization utilities with std mean
    """

    def __init__(self):
        self.mean = 0.
        self.std = 1.

    def fit(self, data):
        self.mean = np.mean(data)
        self.std = np.std(data)

    def transform(self, data):
        mean = paddle.to_tensor(self.mean).type_as(data).to(
            data.device) if paddle.is_tensor(data) else self.mean
        std = paddle.to_tensor(self.std).type_as(data).to(
            data.device) if paddle.is_tensor(data) else self.std
        return (data - mean) / std

    def inverse_transform(self, data):
        mean = paddle.to_tensor(self.mean) if paddle.is_tensor(data) else self.mean
        std = paddle.to_tensor(self.std) if paddle.is_tensor(data) else self.std
        return (data * std) + mean


class ScalerMinMax(object):
    """
    Desc: Normalization utilities with min max
    """

    def __init__(self):
        self.min = 0.
        self.max = 1.

    def fit(self, data):
        self.min = np.min(data, axis=0)
        self.max = np.max(data, axis=0)

    def transform(self, data):
        _min = paddle.to_tensor(self.min).type_as(data).to(
            data.device) if paddle.is_tensor(data) else self.min
        _max = paddle.to_tensor(self.max).type_as(data).to(
            data.device) if paddle.is_tensor(data) else self.max
        data = 1. * (data - _min) / (_max - _min)
        return 2. * data - 1.

    def inverse_transform(self, data, axis=None):
        _min = paddle.to_tensor(self.min) if paddle.is_tensor(data) else self.min
        _max = paddle.to_tensor(self.max) if paddle.is_tensor(data) else self.max
        data = (data + 1.) / 2.
        return 1. * data * (_max - _min) + _min


class CustomDataset(Dataset):
    def __init__(self, file_path, data_type="train"):
        """

        :param file_path:
        :param data_type: train or test
        """
        super().__init__()
        all_data = np.load(file_path)
        data = all_data["data"]
        num, _, _ = data.shape
        data = data.reshape(num, -1)

        self.neighbors = all_data['neighbors']
        self.areasoverlengths = all_data['areasoverlengths']
        self.dirichletnodes = all_data['dirichletnodes']
        self.dirichleths = all_data['dirichletheads']
        self.Qs = np.zeros([all_data['coords'].shape[-1]])
        self.val_data = all_data["test_data"]

        self.data_type = data_type

        self.train_len = int(num * 0.8)
        self.test_len = num - self.train_len

        self.train_data = data[:self.train_len]
        self.test_data = data[self.train_len:]

        self.scaler = ScalerStd()
        self.scaler.fit(self.train_data)

        self.train_data = self.scaler.transform(self.train_data)
        self.test_data = self.scaler.transform(self.test_data)

    def __getitem__(self, idx):
        if self.data_type == "train":
            return self.train_data[idx]
        else:
            return self.test_data[idx]

    def __len__(self):
        if self.data_type == "train":
            return self.train_len
        else:
            return self.test_len


if __name__ == '__main__':
    train_data = CustomDataset(file_path="data/gaussian_train.npz", data_type="train")
    test_data = CustomDataset(file_path="data/gaussian_train.npz", data_type="test")
    train_loader = DataLoader(train_data, batch_size=128, shuffle=True, drop_last=True,
                              num_workers=0)
    test_loader = DataLoader(test_data, batch_size=128, shuffle=True, drop_last=True,
                             num_workers=0)

    for i, data_item in enumerate(train_loader()):
        print(data_item)

        if i == 2:
            break
