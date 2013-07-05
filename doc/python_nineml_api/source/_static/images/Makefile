

all: figs

figs: iaf_component_im.png coba_component_im.png iaf_coba2_component_im.png AL_UL_Overview.png SimpleRegimeGraph.png

iaf_component_im.png: srcs/iaf_component.svg
	convert -depth 16 -background transparent -resize 35% -density 300 srcs/iaf_component.svg iaf_component_im.png

coba_component_im.png: srcs/coba_component.svg
	convert -depth 16 -background transparent -resize 35% -density 300 srcs/coba_component.svg coba_component_im.png

iaf_coba2_component_im.png: srcs/iaf_coba2_component_simplified.svg
	convert -depth 16 -background transparent -resize 35% -density 300 srcs/iaf_coba2_component_simplified.svg iaf_coba2_component_im.png

AL_UL_Overview.png: srcs/AL_UL_Overview.svg
	convert -depth 16 -background transparent -resize 15% -density 300 srcs/AL_UL_Overview.svg AL_UL_Overview.png

SimpleRegimeGraph.png: srcs/SimpleRegimeGraph.svg
	convert -depth 16 -background transparent -resize 15% -density 300 srcs/SimpleRegimeGraph.svg SimpleRegimeGraph.png