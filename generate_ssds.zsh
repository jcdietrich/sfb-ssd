#!/usr/bin/env zsh
IFS=$'\n'
for SSD in $('ls' -1 *.(png|jpg|jpeg) | grep -v '_viz\.png$' | grep -v 'screenshot'); do
  ./full_ssd.py "${SSD}"
done
