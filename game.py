from pyboy import PyBoy
from pyboy.plugins.game_wrapper_pokemon_gen1 import GameWrapperPokemonGen1


pyboy = PyBoy('emulation/red.gb')
wrapper = GameWrapperPokemonGen1(pyboy)

while not pyboy.tick():
    wrapper.print()
    pass
pyboy.stop()