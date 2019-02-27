Builds HTML documentation for the Wayland protocol and protocol
extensions.

Usage
-----

```
% git clone https://github.com/jonnylamb/wayland-docs.git
% git clone https://gitlab.freedesktop.org/wayland/wayland.git
% git clone https://gitlab.freedesktop.org/wayland/weston.git
% cd wayland-docs
% make
...
Your protocol HTML starts at:

file://.../wayland-docs/doc/wayland/index.html
file://.../wayland-docs/doc/weston/index.html
```

Notes
-----

This is a heavily modified version the [telepathy-spec
parser](http://cgit.freedesktop.org/telepathy/telepathy-spec/).

Unfortunately the XML files are too radically different to be able to
share parsing code without it being much more complicated or less
smart.