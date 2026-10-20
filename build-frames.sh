#!/usr/bin/env sh
# Rebuild sharp sequences from original movies, keeping the captioned Hero window.
set -eu
for entry in 'hero:play' 'about:work' 'process:move' 'services:slow' 'contact:hello'; do
  node_name=${entry%%:*}
  source_name=${entry#*:}
  for variant in desktop mobile; do
    if [ "$variant" = desktop ]; then frame_width=828; else frame_width=480; fi
    mkdir -p "frames/$node_name/$variant"
    ffmpeg -y -threads 1 -filter_threads 1 -i "media/$source_name.mp4" -an \
      -vf "fps=24,scale=$frame_width:-2" -c:v libwebp -q:v 72 -compression_level 2 \
      "frames/$node_name/$variant/frame_%04d.webp"
    if [ "$node_name" = hero ]; then
      ffmpeg -y -threads 1 -filter_threads 1 -ss 6 -i media/play-captioned-large-web.mp4 -t 2.25 -an \
        -vf "fps=24,scale=$frame_width:-2" -c:v libwebp -q:v 72 -compression_level 2 \
        -start_number 145 "frames/$node_name/$variant/frame_%04d.webp"
    fi
  done
done
