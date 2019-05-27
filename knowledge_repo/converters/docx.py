import os
import re
import shutil
import tempfile

from ..converter import KnowledgePostConverter


class DocxConverter(KnowledgePostConverter):

    _registry_keys = ['docx']

    @property
    def dependencies(self):
        # Dependencies required for this converter on top of core knowledge-repo dependencies
        return ['pypandoc']
    #     , 'xml', 'zipfile', 'datetime'] ## no need, basically: built in. And: what are the distribution names so pkg_resources.find_distributions can finde those packages?

    def from_file(self, filename, **opts):
        self.tmp_dir = wd = tempfile.mkdtemp()
        target_file = os.path.join(wd, 'post.md')
        
        import pypandoc
        pypandoc.convert_file(
            filename,
            format='docx',
            to='markdown-grid_tables',
            outputfile=target_file,
            extra_args=[
                '--standalone',
                '--wrap=none',
                '--extract-media={}'.format(wd)
            ]
        )

        with open(target_file) as f:
            md = f.read()

        # Image embeddings exported from docx files have fixed sizes in inches
        # which browsers do not understand. We remove these annotations.
        md = re.sub(r'(\!\[[^\]]+?\]\([^\)]+?\))\{[^\}]+?\}', lambda m: m.group(1), md)

        """ 
        Get Header for Knowledge Repo. 
        Necessary are: {'title', 'tldr', 'created_at', 'authors'} - from code (from docs: tags seems to be required too)
        Possible are: {'tags','updated_at','path','thumbnail','private', 'allowed_group'}
        """
        
        title = md.splitlines()[0]
        
        import zipfile
        import xml.etree.ElementTree as ET
        
        prefixes=[
            '{http://purl.org/dc/elements/1.1/}',
            '{http://purl.org/dc/terms/}',
            '{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}',
            '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        ]
        
        with zipfile.ZipFile(filename) as docx:
            docProps = ET.XML(docx.read('docProps/core.xml'))
            modifier = None
            creator = None
            modified = None
            for prefix in prefixes:
                if modifier is None:
                    modifier = docProps.find(prefix+'lastModifiedBy')
                if creator is None:
                    creator = docProps.find(prefix+'creator')
                if modified is None:
                    modified = docProps.find(prefix+'modified')
        authors = [modifier.text, creator.text]
        
        from datetime import datetime
        dtobj = datetime.strptime(modified.text.replace('T',' ').replace('Z',''),'%Y-%m-%d %H:%M:%S')
        
        created_at = dtobj
        
        headers = {
            'title': title,
            'tldr': title,
            'created_at': created_at,
            'authors': authors,
            'path': '_'.join(title.split(' ')[:6])#.encode(encoding='utf-8', errors='replace').decode(encoding='cp1252',errors='strict')
        }
        
        # Write markdown content to knowledge post (images will be extracted later)
        self.kp_write(md, headers)
#         self.kp.path
#         self.kp.write(md, headers)

    def cleanup(self):
        if hasattr(self, 'tmp_dir'):
            shutil.rmtree(self.tmp_dir)
            del self.tmp_dir
