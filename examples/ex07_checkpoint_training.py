import fesl
from fesl import printout
from data_repo_path import get_data_repo_path
data_path = get_data_repo_path()+"Al256_reduced/"

"""
ex07_checkpoint_training.py: Shows how a training run can be paused and 
resumed.
"""


def run_example07(desired_loss_improvement_factor=1):
    ####################
    # PARAMETERS
    # All parameters are handled from a central parameters class that
    # contains subclasses.
    ####################

    test_parameters = fesl.Parameters()
    # Currently, the splitting in training, validation and test set are
    # done on a "by snapshot" basis. Specify how this is
    # done by providing a list containing entries of the form
    # "tr", "va" and "te".
    test_parameters.data.data_splitting_type = "by_snapshot"
    test_parameters.data.data_splitting_snapshots = ["tr", "va", "te"]

    # Specify the data scaling.
    test_parameters.data.input_rescaling_type = "feature-wise-standard"
    test_parameters.data.output_rescaling_type = "normal"

    # Specify the used activation function.
    test_parameters.network.layer_activations = ["ReLU"]

    # Specify the training parameters.
    # We only train for an odd number of epochs here, and train for
    # the rest after the checkpoint has been loaded.
    test_parameters.running.max_number_epochs = 8
    test_parameters.running.mini_batch_size = 40
    test_parameters.running.learning_rate = 0.00001
    test_parameters.running.trainingtype = "Adam"

    # We checkpoint the training every 5 epochs and save the results
    # as "ex07".
    test_parameters.running.checkpoints_each_epoch = 5
    test_parameters.running.checkpoint_name = "ex07"

    ####################
    # DATA
    # Add and prepare snapshots for training.
    ####################

    data_handler = fesl.DataHandler(test_parameters)

    # Add a snapshot we want to use in to the list.
    data_handler.add_snapshot("Al_debug_2k_nr0.in.npy", data_path,
                              "Al_debug_2k_nr0.out.npy", data_path,
                              output_units="1/Ry")
    data_handler.add_snapshot("Al_debug_2k_nr1.in.npy", data_path,
                              "Al_debug_2k_nr1.out.npy", data_path,
                              output_units="1/Ry")
    data_handler.add_snapshot("Al_debug_2k_nr2.in.npy", data_path,
                              "Al_debug_2k_nr2.out.npy", data_path,
                              output_units="1/Ry")
    data_handler.prepare_data()
    printout("Read data: DONE.")

    ####################
    # NETWORK SETUP
    # Set up the network and trainer we want to use.
    # The layer sizes can be specified before reading data,
    # but it is safer this way.
    ####################

    test_parameters.network.layer_sizes = [data_handler.get_input_dimension(),
                                           100,
                                           data_handler.get_output_dimension()]

    # Setup network and trainer.
    test_network = fesl.Network(test_parameters)
    test_trainer = fesl.Trainer(test_parameters, test_network, data_handler)

    printout("Network setup: DONE.")

    ####################
    # TRAINING
    # Train the network. After training, load from the last checkpoint
    # and train for more epochs.
    ####################

    printout("Starting training.")
    test_trainer.train_network()
    printout("Training: DONE.")

    loaded_params, loaded_network, new_datahandler, new_trainer = \
        fesl.Trainer.resume_checkpoint("ex07")

    # Note that this means the actual total number of epochs,
    # not the ones trained after loading. That is, if we trained
    # 8 before, but checkpointed every 5 epochs, we will now train
    # for 15.
    loaded_params.running.max_number_epochs = 20
    new_trainer.train_network()
    printout("Training 2.0: DONE.")

    ####################
    # RESULTS.
    # Print the used parameters and check whether the loss decreased enough.
    ####################

    printout("Parameters used for this experiment:")
    test_parameters.show()

    if desired_loss_improvement_factor*test_trainer.initial_test_loss\
            < new_trainer.final_test_loss:
        return False
    else:
        return True


if __name__ == "__main__":
    if run_example07():
        printout("Successfully ran ex07_checkpoint_training.")
    else:
        raise Exception("Ran ex07_checkpoint_training but something was off."
                        " If you haven't changed any parameters in "
                        "the example, there might be a problem with your"
                        " installation.")
