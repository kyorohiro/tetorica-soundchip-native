"""SCSP catalog guards, preserving historical PS1-only releases."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import test_ps1_instrument_release as ps1

ROOT = Path(__file__).resolve().parents[1]


class ScspInstrumentReleaseTests(unittest.TestCase):
    def setUp(self):
        self.helper = ps1.Ps1InstrumentReleaseTests(methodName='runTest')
        self.helper.setUp()
        self.addCleanup(self.helper.doCleanups)
        h = self.helper
        for name, document in [('source_inventory', h.inventory), ('native_inventory', h.native), ('chips', h.catalog)]:
            record = next(item for item in json.loads((ROOT/f'catalog/{name}.json').read_text())['instruments'] if item['id'] == 'scsp')
            document['instruments'].append(copy.deepcopy(record))
        record, device = h.inventory['instruments'][1], h.native['instruments'][1]
        paths = set(record['sourceFiles']+record['licenseFiles']+record['buildFiles']+device['sourceFiles']+device['buildFiles'])
        for name in paths:
            h.helper.write(name, 'Fixture '+name+'\n')
        # Shared build paths are not component hashes; original PS1 records stay valid.
        h.inventory['components'].append({'id': 'fixture-scsp', 'sourceFiles': record['sourceFiles'], 'licenseFiles': record['licenseFiles'],
            'files': [{'path': name, 'originPath': name, 'sha256': hashlib.sha256((h.root/name).read_bytes()).hexdigest()}
                      for name in record['sourceFiles']+record['licenseFiles']]})
        h.save()

    def test_scsp_does_not_change_generic_chip_ids(self):
        h = self.helper
        result = ps1.sdk_common.check_collection(h.root)
        self.assertEqual(result['chips'], 24)
        self.assertEqual(result['instruments'], 2)
        ps1.checker.audit_catalog(h.root)

    def test_duplicate_or_missing_scsp_record_is_rejected(self):
        h = self.helper
        h.native['instruments'].append(copy.deepcopy(h.native['instruments'][1]))
        h.rejected('inventory')
        h.native['instruments'] = h.native['instruments'][:1]
        h.rejected('inventory')

    def test_scsp_sources_require_hash_provenance(self):
        self.helper.inventory['components'][-1]['files'].pop()
        self.helper.rejected('hash provenance')

    def test_scsp_cannot_substitute_an_unrelated_native_target(self):
        h = self.helper
        h.native['instruments'][1]['target'] = 'tetorica_native_ps1_spu'
        h.catalog['instruments'][1]['native'] = copy.deepcopy(h.native['instruments'][1])
        h.rejected('Native target/header')


if __name__ == '__main__':
    unittest.main()
