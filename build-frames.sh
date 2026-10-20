#!/usr/bin/env sh
# Development helper. ffmpeg is required only when rebuilding the supplied frames.
set -eu
for entry in 'hero:play-captioned-large-web' 'about:work-web' 'process:move-web' 'services:slow-web' 'contact:hello-web'; do
  node_name=${entry%%:*}
  source_name=${entry#*:}
  for variant in desktop mobile; do
    if [ "$variant" = desktop ]; then frame_width=960; else frame_width=480; fi
    mkdir -p "frames/$node_name/$variant"
    ffmpeg -y -threads 2 -filter_threads 1 -i "media/$source_name.mp4" -an \
      -vf "fps=24,scale=$frame_width:-2" -c:v libwebp -q:v 70 -compression_level 3 \
      "frames/$node_name/$variant/frame_%04d.webp"
  done
done
