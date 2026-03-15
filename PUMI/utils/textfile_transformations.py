def drop_first_line(in_file):
    import os

    with open(in_file, 'r') as fin:
        data = fin.read().splitlines(True)

    fname = os.path.split(in_file)[-1]
    with open(fname, 'w') as fout:
        fout.writelines(data[1:])  # don't write the first line into the new file
        return os.path.join(os.getcwd(), fname)