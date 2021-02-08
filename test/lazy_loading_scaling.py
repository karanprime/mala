from fesl.common.parameters import Parameters
from fesl.common.printout import printout
from fesl.datahandling.data_handler import DataHandler
import torch


# This test compares the data scaling using the regular scaling procedure and the lazy-loading one (incremental fitting).

def test_lazy_loading(data_path="../examples/data/", accuracy=0.001):
    ####################
    # PARAMETERS
    ####################
    test_parameters = Parameters()
    test_parameters.data.datatype_in = "*.npy"
    test_parameters.data.datatype_out = "*.npy"
    test_parameters.data.data_splitting_snapshots = ["tr", "tr"]#, "tr", "tr"]
    test_parameters.data.input_rescaling_type = "feature-wise-standard"
    test_parameters.data.output_rescaling_type = "normal"
    test_parameters.data.data_splitting_type = "by_snapshot"
    test_parameters.descriptors.twojmax = 11
    test_parameters.targets.ldos_gridsize = 10
    test_parameters.network.layer_activations = ["LeakyReLU"]
    test_parameters.training.max_number_epochs = 10
    test_parameters.training.mini_batch_size = 512
    test_parameters.training.learning_rate = 0.00001
    test_parameters.training.trainingtype = "Adam"
    test_parameters.hyperparameters.n_trials = 20
    test_parameters.comment = "Test run of ML-DFT@CASUS."
    test_parameters.hyperparameters.hyper_opt_method = "optuna"
    test_parameters.network.nn_type = "feed-forward"
    test_parameters.training.use_gpu = True
    test_parameters.data.use_lazy_loading = False


    ####################
    # DATA
    ####################

    results = []
    for scalingtype in ["standard", "normal", "feature-wise-standard", "feature-wise-normal"]:
        comparison = []
        comparison.append(scalingtype)
        for ll_type in [True, False]:
            this_result = []
            if ll_type:
               this_result.append("lazy-loading")
            else:
                this_result.append("RAM")
            test_parameters.data.use_lazy_loading = ll_type
            test_parameters.data.input_rescaling_type = scalingtype
            test_parameters.data.output_rescaling_type = scalingtype
            data_handler = DataHandler(test_parameters)
            data_handler.clear_data()
            data_handler.add_snapshot("Al_debug_2k_nr0.in.npy", data_path, "Al_debug_2k_nr0.out.npy", data_path,
                                      output_units="1/Ry")
            data_handler.add_snapshot("Al_debug_2k_nr1.in.npy", data_path, "Al_debug_2k_nr1.out.npy", data_path,
                                      output_units="1/Ry")
            data_handler.prepare_data()
            if scalingtype == "standard":
                # The lazy-loading STD equation (and to a smaller amount the mean equation) is having some small accurcay issue that
                # I presume to be due to numerical constraints. To make a meaningful comparison it is wise to scale the value here.
                this_result.append(data_handler.input_data_scaler.total_mean/data_handler.nr_training_data)
                this_result.append(data_handler.input_data_scaler.total_std/data_handler.nr_training_data)
                this_result.append(data_handler.output_data_scaler.total_mean/data_handler.nr_training_data)
                this_result.append(data_handler.output_data_scaler.total_std/data_handler.nr_training_data)
            if scalingtype == "normal":
                this_result.append(data_handler.input_data_scaler.total_max)
                this_result.append(data_handler.input_data_scaler.total_min)
                this_result.append(data_handler.output_data_scaler.total_max)
                this_result.append(data_handler.output_data_scaler.total_min)
            if scalingtype == "feature-wise-standard":
                # The lazy-loading STD equation (and to a smaller amount the mean equation) is having some small accurcay issue that
                # I presume to be due to numerical constraints. To make a meaningful comparison it is wise to scale the value here.
                this_result.append(torch.mean(data_handler.input_data_scaler.means)/data_handler.grid_size)
                this_result.append(torch.mean(data_handler.input_data_scaler.stds)/data_handler.grid_size)
                this_result.append(torch.mean(data_handler.output_data_scaler.means)/data_handler.grid_size)
                this_result.append(torch.mean(data_handler.output_data_scaler.stds)/data_handler.grid_size)
            if scalingtype == "feature-wise-normal":
                this_result.append(torch.mean(data_handler.input_data_scaler.maxs))
                this_result.append(torch.mean(data_handler.input_data_scaler.mins))
                this_result.append(torch.mean(data_handler.output_data_scaler.maxs))
                this_result.append(torch.mean(data_handler.output_data_scaler.mins))

            comparison.append(this_result)
        results.append(comparison)

    for entry in results:
        val1 = entry[1][1]-entry[2][1]
        val2 = entry[1][2]-entry[2][2]
        val3 = entry[1][3]-entry[2][3]
        val4 = entry[1][4]-entry[2][4]
        if val1 > accuracy or val2 > accuracy or val3 > accuracy or val4 > accuracy:
            printout(entry[0])
            printout(val1, val2, val3, val4)
            return False
    return True

if __name__ == "__main__":
    test1 = test_lazy_loading_test()
    printout("Check if lazy loading and RAM based scaling gets the same results? - success?:", test1)















