from setuptools import setup, find_packages

setup(name='stochastic_service_composition',
      version='0.1.0',
      description='Implementation of stochastic service composition.',
      license='MIT',
      packages=find_packages(include='stochastic_service_composition*'),
      zip_safe=False,
      install_requires=[
            "numpy",
            "graphviz",
            "websockets",
            "paho-mqtt",
            "requests",
            "connexion[swagger-ui]",
            "logaut",
            "pythomata",
            "flask",
            "aiohttp",
            "aiohttp_jinja2",
            "mdp_dp_rl @ git+https://github.com/luusi/mdp-dp-rl.git#egg=mdp_dp_rl",
            "memory-profiler",
            "tqdm"
      ]
      )
