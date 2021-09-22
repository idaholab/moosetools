#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html
import xml.etree.ElementTree as xml
from .MooseDeepDiff import MooseDeepDiff
from moosetools import mooseutils

def compare_xml(file_0, file_1, **kwargs):
    #mooseutils.validate_extension(file_0, file_1, extension='.xml', raise_on_error=True)
    mooseutils.validate_paths_exist(file_0, file_1, raise_on_error=True)

    xml_0 = xml.parse(file_0).getroot()
    xml_1 = xml.parse(file_1).getroot()

    return MooseDeepDiff(xml_0, xml_1, **kwargs)
