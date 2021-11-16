# Sancty
Sancty is an extension to jquast/blessed for simple editor-like terminal apps

### Usage

Sancty has two major components, `Reader` (which follows the `ReaderProtocol`) and `Renderer` (which follows the `RendererProtocol`). As you are free to choose your own communication channel and event loop/threading architecture, these do not work out of the box. For implementations that work out of the box, take a look at `ProcessReader` and `ProcessRenderer`, which use standard `multiprocessing` classes to each run on their own thread. You can also spin up a basic editor by running `start_terminal()`.

If you don't want to customize the run architecture, but _do_ want to customize the `Reader` and `Renderer` classes, simply extend them (but be sure to still conform to their respective protocols) and pass the classes as variables to `start_terminal()`.

You can also pass a custom `replace_dict`, which is a dictionary of all possible `\\` commands. By default, the key swill correspond to strings that will be replaced by the value strings, but if the key is an integer, a custom `special_slash_fn` can also be passed to perform arbitrary transformations of the render array. Note that all negative numbers are reserved for this program.

#### Default `\\` commands

```python
default_replace_dict = {
    "clr": (-1, "Clears all text"),
    "help": (-2, "Shows all slash commands"),
}
```