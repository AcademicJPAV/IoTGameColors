import os

mapLabels = {
    "Pyro": 0,
    "Hydro": 1,
    "Electro": 2,
    "Cryo": 3,
    "Dendro": 4
}

for directory in os.listdir("data"):
    if os.path.isdir(os.path.join("data", directory)):
        name_split = directory.split("_")
        labels = [mapLabels[label] for label in mapLabels if label in name_split]

        for file in os.listdir(os.path.join("data", directory)):
            if file.endswith(".txt"):
                linhas = []
                with open(os.path.join("data", directory, file),'r',encoding='utf-8') as fileIO:
                    linhas.extend(line.strip() for line in fileIO)
                with open(os.path.join("data", directory, file),'w',encoding='utf-8') as fileIO:
                    for i in range(labels.__len__()):
                        linha_split = linhas[i].split()
                        linha = f"{labels[i]} {linha_split[1]} {linha_split[2]} {linha_split[3]} {linha_split[4]}"
                        fileIO.write(linha + "\n")
