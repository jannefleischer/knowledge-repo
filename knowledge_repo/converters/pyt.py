from os import path
from ast import parse, ClassDef, FunctionDef
from ..converter import KnowledgePostConverter
# import git
# from shutil import copy2

import xml.etree.ElementTree as ET
from html import unescape

class PytConverter(KnowledgePostConverter):
    '''
    Use this as a template for new KnowledgePostConverters.
    '''
    _registry_keys = ['pyt']

    @property
    def dependencies(self):
        # Dependencies required for this converter on top of core knowledge-repo dependencies
        return []

    def from_file(self, filename, **opts):
        with open(filename) as fi:
            """ 
            Get Header for Knowledge Repo. 
            Necessary are: {'title', 'tldr', 'created_at', 'authors'} - from code (from docs: tags seems to be required too)
            Possible are: {'tags','updated_at','path','thumbnail','private', 'allowed_group'}
            """
            
            """
            using ast to determine which tools are in the toolbox
            """
            node = parse(fi.read())
            cls = [n for n in node.body if isinstance(n, ClassDef)]
            for c in cls:
                if c.name=='Toolbox':
                    fns = [n for n in c.body if isinstance(n, FunctionDef)]
                    for f in fns:
                        if f.name=='__init__':
                            first=f.body[0].lineno
                            last=f.body[-1].lineno
                            fi.seek(0)
                            excerpt=''
                            for i, line in enumerate(fi):
                                if i>=first:
                                    if 'tools' in line:
                                        tools = line.split('[',1)[1].rsplit(']',1)[0].split(',')
                                        break
                                if i==last:
                                    raise Exception('tools not found')
                    break
            
            """
            Generate the paths to the documentation-xml-files
            """
            pyt_docfiles = [path.join( path.dirname(filename), path.basename(filename)+'.xml')]
            for t in tools:
                pyt_docfiles.append(path.join( path.dirname(filename), path.basename(filename).rsplit('.pyt')[0]+'.'+t+'.pyt.xml'))
            
            
            """
            Convert ESRI-XML-Help-File to a .md which can be imported to the Knowledge Repo
            DONE: Extracted Information
            TODO: Write Informations to .md
            """
            
            for x in pyt_docfiles:
                root = ET.parse(x).getroot()
                createdate = root.find('Esri').find('CreaDate').text
                #createtime = root.find('Esri').find('CreaTime').text
                moddate = root.find('Esri').find('ModDate').text
                #modtime = root.find('Esri').find('ModTime').text
                if root.find('toolbox') is not None:
                    toolboxname = {
                        'name': root.find('toolbox').get('name'),
                        'alias': root.find('toolbox').get('alias')
                    }
                else:
                    toolname = {
                        'name': root.find('tool').get('name'),
                        'displayname': root.find('tool').get('displayname'),
                        'toolboxalias': root.find('tool').get('toolboxalias')
                    }
                    params = root.find('tool').find('parameters').findall('param')
                    paramtexts = []
                    for p in params:
                        paramtext = {}
                        hilfeText = ''
                        for ps in ET.fromstring(unescape(p.find('dialogReference').text)).iter('P'):
                            hilfeText += unescape(ET.tostring(ps).decode().replace('<SPAN>','').replace('</SPAN>','').replace('<P>','').replace('</P>','')) + '\n'
                        paramtext['name'] = p.get('name')
                        paramtext['displayname'] = p.get('displayname')
                        paramtext['datatype'] = p.get('datatype')
                        paramtext['hilfeText'] = hilfeText
                        paramtexts.append(paramtext)
                        
            """
            import .md-File to Knowledge-Repo and add all Files to src-tree
            """
#             fi.seek(0)
#             self.kp_write(fi.read())

    def from_string(self, filename, **opts):
        raise NotImplementedError

    def to_file(self, filename, **opts):
        raise NotImplementedError

    def to_string(self, **opts):
        raise NotImplementedError
