#!/bin/bash

version=1.0

# Reads the list of source files, excludes, and the destination directory
my_fullpath=$0
my_dir=$(dirname $my_fullpath)

list_path="$my_dir"/"paudio_backup/list_of_files"
exclude_path="$my_dir"/"paudio_backup/excludes"

# this includes the $dest_dir varibale
dest_path="$my_dir"/"paudio_backup/destination"
source $dest_path

if [[ ! -d $dest_dir ]]; then
    echo "Destination base directory not found: ""$dest_dir"
    exit 1
fi

# Creates the base folder of the copies on the destination.
# A separate subfolder with the hostname will be used.
dest_dir+=$HOSTNAME"/"
timestamp=$(date +%Y%m%d-%H%M)
echo ""
if   [[ $1 == *"-d"* ]]; then
    dest_dir+=$timestamp"/"
    echo ""

elif [[ $1 == *"-n"* ]]; then
    echo""

else
    echo "paudio_backup.sh v""$version"
    echo
    echo "A simple script to save your important files."
    echo
    echo "Configure what to backup, what to exclude, and where here:"
    echo
    echo "      paudio_backup/list_of_files"
    echo "      paudio_backup/excludes"
    echo "      paudio_backup/destination"
    echo
    echo "CURRENT destination is:"
    echo
    echo "      ==> ""$dest_dir"
    echo
    echo "Usage: paudio_backup.sh  --dated | --nodated"
    echo
    echo "       --dated will make a dated subdirectory in destination"
    echo
    exit 0
fi


if ! mkdir -p $dest_dir ; then
    echo ""
    echo "Does the destination folder is mounted?"
    echo ""
    exit 0
fi

echo "DESTINATION: "$dest_dir
echo ""


# Do copy items
# -r prevents backslash escapes to be interpreted by read command
while read -r line; do

    # Removing comments:
    item=$(echo "$line" | cut -d'#' -f1)

    # Removing trailing spaces
    while [[ $item == *" " ]]; do
        item=${item%% }
    done

    # Skip blank lines
    if [[ ! "$item" ]]; then
        continue
    fi

    echo "ORIGIN:  ""$item"

    # Al introducir el punto /./ en la ruta de origen,
    # le estás marcando a rsync el "punto de partida" a partir del cual
    # debe replicar las carpetas en el destino:
    # --relative conserva la ruta relativa del origen
    # -rt es como -a (archive) pero compatible con filesystem NO Unix como un pincho FAT
    # --modify-window=1 usa la marca de tiempo como FAT de 1 segundo
    # --no-links omite los symlink en origen

    rsync -rt --relative --modify-window=1 --no-links \
        --exclude-from="$exclude_path" \
        /./"$item" "$dest_dir"

done < "$list_path"


echo ""
echo "END."
echo ""

