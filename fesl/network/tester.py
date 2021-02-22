import numpy as np
import torch
from torch import optim
from torch.utils.data import DataLoader
from fesl.common.parameters import printout
from .runner import Runner
try:
    import horovod.torch as hvd
except ModuleNotFoundError:
    # Warning is thrown by Parameters class
    pass
import time

class Tester(Runner):
    """A class for testing a neural network. It enables easy inference throughout a test set."""

    def __init__(self, p):
        # copy the parameters into the class.
        super(Tester, self).__init__(p)
        self.data = None
        self.test_data_loader = None
        self.number_of_batches_per_snapshot = 0

    def set_data(self, network, data):
        self.prepare_to_run()
        self.data = data
        self.network = network
        if self.use_horovod:
            self.parameters.sampler["test_sampler"] = torch.utils.data.distributed.DistributedSampler(data.test_data_set,
                                                                                                  num_replicas=hvd.size(),
                                                                                                  rank=hvd.rank())
        # We will use the DataLoader iterator to iterate over the test data. But since we only want the data per
        # snapshot, we need to make sure the batch size is compatible with that.
        self.__check_and_adjust_batch_size(data.grid_size)
        self.test_data_loader = DataLoader(data.test_data_set, batch_size=self.batch_size * 1,
                                      sampler=self.parameters.sampler["test_sampler"], **self.parameters.kwargs,
                                           shuffle=False)
        self.number_of_batches_per_snapshot = int(data.grid_size / self.batch_size)



    def test_snapshot(self, snapshot_number):
        self.data.prepare_for_testing()
        if self.data.parameters.use_lazy_loading:
            actual_outputs = (self.data.test_data_set[snapshot_number * self.data.grid_size:(snapshot_number + 1) * self.data.grid_size])[1]
        else:
            actual_outputs = self.data.output_data_scaler.inverse_transform(
                (
                self.data.test_data_set[snapshot_number * self.data.grid_size:(snapshot_number + 1) * self.data.grid_size])[
                    1],
                as_numpy=True)

        predicted_outputs = np.zeros((self.data.grid_size, self.data.get_output_dimension()))

        offset = snapshot_number * self.data.grid_size
        for i in range(0, self.number_of_batches_per_snapshot):
            inputs, outputs = self.data.test_data_set[offset+(i * self.batch_size):offset+((i + 1) * self.batch_size)]
            if self.use_gpu:
                inputs = inputs.to('cuda')
            predicted_outputs[i * self.batch_size:(i + 1) * self.batch_size, \
                :] = self.data.output_data_scaler.inverse_transform(self.network(inputs).to('cpu'), as_numpy=True)

        return actual_outputs, predicted_outputs


    def __check_and_adjust_batch_size(self, datasize):
        if datasize % self.batch_size != 0:
            old_batch_size = self.batch_size
            while datasize % self.batch_size != 0:
                self.batch_size += 1
            printout("Had to readjust batch size from", old_batch_size, "to", self.batch_size)



    # def process_mini_batch(self, network, input_data, target_data):
    #     prediction = network.forward(input_data)
    #     loss = network.calculate_loss(prediction, target_data)
    #     loss.backward()
    #     self.optimizer.step()
    #     self.optimizer.zero_grad()
    #     return loss.item()
    #
    # def validate_network(self, network, vdl):
    #     network.eval()
    #     validation_loss = []
    #     with torch.no_grad():
    #         for x, y in vdl:
    #             if self.use_gpu:
    #                 x = x.to('cuda')
    #                 y = y.to('cuda')
    #             prediction = network(x)
    #             validation_loss.append(network.calculate_loss(prediction, y).item())
    #
    #     return np.mean(validation_loss)
    #
    # def average_validation(self,val,name):
    #     tensor= torch.tensor(val)
    #     avg_loss=hvd.allreduce(tensor,name=name, op=hvd.Average)
    #     return avg_loss.item()
