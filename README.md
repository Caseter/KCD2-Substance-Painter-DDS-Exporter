<h1 align="center">
KCD2 Substance Painter DDS Exporter
</h1>

# KCD2 Mod Page
https://www.nexusmods.com/kingdomcomedeliverance2/mods/1029

A Substance Painter DDS export plugin to automate conversion to DDS.

Original idea made by Emil for Starfield - https://github.com/emomilol1213/Substance-Painter-DDS-Exporter. Repurposed and bastardised by Caseter

No more spending 20 minutes manually converting those 20 different maps to DDS.

# Installation:
Extract the KCD2-dds-exporter.py into your Substance Painter Plugin folder:
<pre>
C:\Users\username\Documents\Adobe\Adobe Substance 3D Painter\python\plugins
</pre>

(Can also be found using the Python > Plugins Folder button in the top row)

Direct the tool to your RC folder (inside the official mod tools Tool>RC by default). Do not use old versions of RC as it will have some issues.

## Export preset:
Move the Kingdom Come Deliverance 2 Export.spexp from the optional files to this folder: 
<pre>
C:\Users\username\Documents\Adobe\Adobe Substance 3D Painter\assets\export-presets
</pre>

## Working with alpha (from diffuse):

Drag and drop the pbr-spec-gloss-alpha-blending.glsl file into your assets bar in Substance.

Put the KCD2_Project_Template.spt file in the following folder:
<pre>
C:\Users\username\Documents\Adobe\Adobe Substance 3D Painter\assets\templates
</pre>

Add a fill layer to your project with all of your original textures.

Add a new fill layer and select only opacity. Add your diff layer into the opacity slot.

![plugin widget](https://i.gyazo.com/b161906b3c7d14c159174dfc589d9448.png)

Add a levels effect to the fill layer, and apply to opacity. Change the output maximum to 1 (bottom left of the graph) so that all of your texures non-transparent areas appear as white.

![plguin widget](https://i.gyazo.com/a5f96c3ce0012ec5874b6b053b49495c.png)

Add another fill layer BELOW the previous opacity layer and set the slider to 0 so the transparent areas turn black.

![plugin widget](https://i.gyazo.com/6ffdc8f225ef0a6e153c71aad2ab01a0.png)

You now have transparency working and this will export into your diffuse using the export template.

## Enable the KCD2-DDS-Exporter under the Python menu
First time running the plugin it will ask you what folder the rc.exe is located in via a UI pop-up. This will create a KCD2-DDS-Exporter-PluginSettings.ini in the plugin folder with the settings saved.

![plugin widget](https://i.gyazo.com/4a6f268e6204984fb3e3c192a38698e1.jpg)

# Dependencies:
Currently all installed automatically. Relies on Pillow & imageio via Python.

# Compatibility
Tested with Substance Painter 10.1.2 (2025)

## Support
Please reach out on the KCD2 modding Discord if you have issues.

https://discord.gg/az7YzHeJNy
