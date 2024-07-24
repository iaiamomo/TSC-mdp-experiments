# Industrial API composition via Policy-based techiques - Chip Supply Chain Case Study

Implementation of a tool to compose Industral API of the manufacturing actorsvia Markov Decision Processes.

Results of the experiments can be found in [chip_experimental_results](chip_experimental_results). Some results referring to the computation of the composition MDP can be null as we serialize the MDP in a pickle file so we do not have to recompute it each time.

Graphical representations of the target and the composition MDP (`xsmall` size) can be found in [debug](docs/notebooks/debug.ipynb) notebook.

## How to replicate the experiments
The experiments can be replicated either using Docker or from source code. We suggest to use Docker.

#### Configuration file
The configuration file [config.json](docs/notebooks/config.json) containing basic information needed to run the experiments. An example with information of the key-value pairs is given below.
```json
{
    "mode": "automata",   //type of the target, accepted values are ["automata", "ltlf"]
    "size": "xsmall",      //size of the case study, accepted values are ["xsmall", "small", "medium", "large"]
    "gamma": 0.9,         //gamma value for policy computation
    "phase": 2,           //in this case study such value is not used, you can skip this
    "serialize": false,   //if you want to save the composition in a pickle file, accepted value are [true, false], you can skip this
    "version": "v5",      //version of the case study, you can skip this
}
```

### Use the Docker image

1. Build the image from the [Dockerfile](Dockerfile):
  ```sh
  docker build -t mdp_controller .
  ```

2. Run a new container and open a terminal from the created image:
  ```sh
  docker run mdp_controller bash
  ```

3. Start the controller:
  ```sh
  cd docs/notebooks
  python3 main.py 
  ```

**Please note:** the configuration file conf.json contains the basic information needed to run the experiments. The JSON key ``mode`` accept the values ``[automata, ltlf]``, the key ``phase`` accepts ``[1,2]`` values (representing the assortment and manufacturing phases respectively), and the key ``size`` accepts ``[small, manageable1, manageable2, complex]`` values (related to the number of involved actors).

### From the source code

We assume the review uses a UNIX-like machine and that has Python 3.8 installed.

- Set up the virtual environment. 
First, install [Pipenv](https://pipenv-fork.readthedocs.io/en/latest/).
Then:
  ```sh
  pipenv install --dev
  ```
                    
- this command is to start a shell within the Python virtual environment (to be done whenever a new terminal is opened):
  ```sh
  pipenv shell
  ```

- Install the Python package in development mode:
  ```sh
  pip install -e .
  # alternatively:
  # python setup.py develop 
  ```

- To use rendering functionalities, you will also need to install Graphviz. 
  At [this page](https://www.graphviz.org/download/) you will
  find the releases for all the supported platform.

- Run the Controller
  ```sh
  cd docs/notebook
  python main.py
  ```

