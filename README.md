# Orchestration of services in Smart Manufacturing through automated synthesis - Stochastic policy approaches

Repository containing the case studies and the experimental results of the stochastic policy approaches (target automata and LTLf) for the paper "Orchestration of services in Smart Manufacturing through automated synthesis".

## Chip

## Ceramic

## Motor

## Experiments

The experiments can be replicated using Docker.

#### Configuration file
The configuration file  `config.json` in each case study folder, contains basic information needed to run the experiments. An example with information of the key-value pairs is given below.
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
