from pywayland.scanner import Protocol

xmldeps = [
    '/usr/share/wayland/wayland.xml',
    '/usr/share/wayland-protocols/staging/ext-foreign-toplevel-list/ext-foreign-toplevel-list-v1.xml',
    '/usr/share/wayland-protocols/staging/ext-workspace/ext-workspace-v1.xml',
]

tlw = 'protocols/ext-foreign-toplevel-workspace-unstable-v1.xml'

dep_protos = [Protocol.parse_file(x) for x in xmldeps]

all_imports = {}

for d in dep_protos:
    print()
    print(d)
    # print(dir(d))
    for i in d.interface:
        print(i.name, d.name)
        all_imports[i.name] = d.name

print()
print("reading", tlw)
print()

pr = Protocol.parse_file(tlw)
for i in pr.interface:
    print(i.name, d.name)
    all_imports[i.name] = pr.name

print("outputting", tlw)
pr.output("./out/", all_imports)

