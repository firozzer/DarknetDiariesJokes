with open("timestamps.txt") as f:
    data = f.read()

data = data.split('\n')
dataUniq = set(data)

dataDic = {}
for dat in dataUniq:
    if dat:
        dat = dat.strip().split()
        dataDic[int(dat[0])] =  dat[1] + " " + dat[2]

sortedDic = dict(sorted(dataDic.items(), key=lambda item: item[0]))

newStr =''
for k,v in sortedDic.items():
    newStr += str(k) + " " + v + "\n"

# to see visually which one is missing
for i in range(47, 125): 
    print(i,sortedDic.get(i, 'YOOOOOOOOOOOOOO'))

with open("tsSorted.txt", 'w') as f:
    f.write(newStr)