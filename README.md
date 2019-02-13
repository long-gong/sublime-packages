# Long's Sublime Text Packages & Configurations

## Dependencies

- Fonts
    - Source Code Pro
    - IBM Plex Mono
    All fonts can be found and downloaded from [Google Font](https://fonts.google.com/)
- [Ghostscript](https://www.ghostscript.com/download/gsdnld.html): required for Windows, if you want to use the customized builder for LaTeXTools 

## Usage

- Step 1: Install `Packet Control`
- Step 2: Find the location of `Packages/User/` folder (you can goto `Packages` by simply using the `Preferences/Browse Packages ...` at the menu bar of Sublime Text). If there is no `User` directory, then you can simply create one. Then,
  ```bash
  git clone https://github.com/long-gong/sublime-packages.git .
  ```
- Step 3: Open sublime text again, those packages will be installed automatically.

## Customization

Some packages have been customized such as [LaTeXTools](https://github.com/SublimeText/LaTeXTools), which will be detailed as follows.

### LaTeXTools

A customized builder is added for LaTeXTools, which can help embed all fonts automatically (avoiding post-processing with Adobe or some other tools).
