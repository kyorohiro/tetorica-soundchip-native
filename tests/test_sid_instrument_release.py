"""SID catalog/raw-WASM isolation guards; synthetic sources, no compiler needed."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import test_ps1_instrument_release as ps1
import package_release


class SidInstrumentReleaseTests(unittest.TestCase):
    def setUp(self):
        self.helper = ps1.Ps1InstrumentReleaseTests(methodName='runTest')
        self.helper.setUp()
        self.addCleanup(self.helper.doCleanups)
        h = self.helper
        for identifier in ('sid', 'sid8580'):
            record = {'id':identifier, 'role':'instrument', 'kind':'CPU-free SID fixture', 'chipIds':[],
                'format':'standalone-wasm', 'outputs':[identifier+'_wasm.wasm'],
                'buildScript':f'scripts/build_{identifier}_wasm.sh',
                'buildFiles':[f'scripts/build_{identifier}_wasm.sh'],
                'sourceFiles':[f'vendor/{identifier}/core.c',f'native/include/tetorica/{identifier}.h'],
                'licenseFiles':[f'vendor/{identifier}/LICENSE']}
            device = {'id':identifier,'role':'instrument','target':f'tetorica_native_{identifier}',
                'cmakeAlias':f'tetorica::{identifier}','publicHeader':f'native/include/tetorica/{identifier}.h',
                'sourceFiles':record['sourceFiles'],'licenseFiles':record['licenseFiles'],'buildFiles':['CMakeLists.txt']}
            for name in set(record['sourceFiles']+record['licenseFiles']+record['buildFiles']+device['buildFiles']):
                h.helper.write(name, 'Fixture '+name+'\n')
            h.inventory['instruments'].append(record)
            h.native['instruments'].append(device)
            h.catalog['instruments'].append({'id':identifier,'native':copy.deepcopy(device),
                'wasm':{'artifacts':[ps1.sdk_common.artifact_descriptor(record)]}})
            h.inventory['components'].append({'id':'fixture-'+identifier,'sourceFiles':record['sourceFiles'],'licenseFiles':record['licenseFiles'],
                'files':[{'path':name,'originPath':name,'sha256':hashlib.sha256((h.root/name).read_bytes()).hexdigest()}
                    for name in record['sourceFiles']+record['licenseFiles']]})
        h.save()

    def test_sid_models_are_separate_instruments_and_preserve_24_chip_ids(self):
        h=self.helper
        self.assertEqual(ps1.sdk_common.check_collection(h.root)['instruments'],3)
        self.assertEqual(ps1.sdk_common.check_collection(h.root)['chips'],24)
        ps1.checker.audit_catalog(h.root)
        self.assertFalse({'sid','sid8580'} & ps1.sdk_common.CHIP_IDS)

    def test_raw_outputs_are_explicit_and_cannot_be_dx7_a_factory_or_an_unsafe_path(self):
        h=self.helper
        for value in [None,[],['msfa.wasm'],['sid_wasm.js','sid_wasm.wasm'],['sid_wasm.wasm']*2,['../sid_wasm.wasm']]:
            with self.subTest(outputs=value):
                h.inventory['instruments'][1]['outputs']=value
                h.rejected('explicit WASM outputs')

    def test_sid_format_role_and_generic_chip_claim_are_rejected(self):
        h=self.helper;record=h.inventory['instruments'][1]
        for key,value in [('format','emscripten-es-module'),('role','application-audio'),('chipIds',['ym2612'])]:
            before=record[key];record[key]=value
            with self.subTest(field=key):h.rejected('separate instrument API')
            record[key]=before

    def test_sid_header_target_and_sources_remain_bound_to_the_snapshot(self):
        h=self.helper
        h.native['instruments'][1]['publicHeader']='native/include/tetorica/ps1_spu.h'
        h.catalog['instruments'][1]['native']=copy.deepcopy(h.native['instruments'][1])
        h.rejected('Native target/header')

    def test_sid_sources_must_have_independent_hash_provenance(self):
        self.helper.inventory['components'][-1]['files'].pop()
        self.helper.rejected('hash provenance')

    def test_dx7_keeps_its_legacy_standalone_filename(self):
        recipe={'id':'dx7','format':'standalone-wasm'}
        self.assertEqual(ps1.sdk_common.artifact_outputs(recipe),['msfa.wasm'])
        self.assertEqual(ps1.checker.artifact_outputs(recipe),['msfa.wasm'])
        for checker,error in [(ps1.sdk_common.artifact_outputs,ValueError),(ps1.checker.artifact_outputs,ps1.checker.AuditError)]:
            with self.assertRaisesRegex(error,'Unsupported standalone'):checker({'id':'unknown','format':'standalone-wasm'})

    def wasm_fixture(self):
        h=self.helper;directory=h.helper.work/'compiled';directory.mkdir()
        records=[]
        for recipe in h.inventory['instruments'][1:]:
            sources=[{'path':name,**ps1.sdk_common.file_record(h.root/name)} for name in sorted(set(recipe['sourceFiles']+recipe['buildFiles']))]
            name=recipe['outputs'][0];(directory/name).write_bytes(b'\0asm\1\0\0\0')
            records.append({'id':recipe['id'],'format':recipe['format'],'sourceFiles':sources,
                'sourceFingerprint':hashlib.sha256(json.dumps(sources,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
                'outputs':[{'path':name,**ps1.sdk_common.file_record(directory/name)}], 'compiler':{'version':'fixture compiler'}})
        (directory/'build-info.json').write_text(json.dumps({'schemaVersion':1,'artifacts':records}))
        archive=h.helper.work/'source.zip';archive.write_bytes(b'audited companion fixture')
        with patch.object(package_release,'ROOT',h.root):payload,extra=package_release.wasm_payload(directory,archive,{},h.inventory)
        released=h.helper.work/'released';released.mkdir()
        for name,data in payload.items():
            target=released/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        return released,extra,archive,directory

    def test_two_raw_wasm_files_package_and_audit_without_js_or_filename_collisions(self):
        released,manifest,archive,_=self.wasm_fixture()
        ps1.checker.audit_wasm(released,manifest,self.helper.root,archive,self.helper.inventory)
        self.assertEqual({file.name for file in (released/'wasm').iterdir()},{'build-info.json','sid_wasm.wasm','sid8580_wasm.wasm'})

    def test_a_raw_recipe_cannot_ship_a_loader_or_duplicate_receipt_output(self):
        released,manifest,archive,directory=self.wasm_fixture()
        info=json.loads((directory/'build-info.json').read_text());record=info['artifacts'][0]
        record['outputs'].append(copy.deepcopy(record['outputs'][0]))
        for root in [directory,released/'wasm']:(root/'build-info.json').write_text(json.dumps(info))
        with patch.object(package_release,'ROOT',self.helper.root),self.assertRaisesRegex(ValueError,'output set'):
            package_release.wasm_payload(directory,archive,{},self.helper.inventory)
        with self.assertRaisesRegex(ps1.checker.AuditError,'missing WASM output'):
            ps1.checker.audit_wasm(released,manifest,self.helper.root,archive,self.helper.inventory)

    def test_raw_wasm_provenance_cannot_drop_a_source_even_with_new_fingerprint(self):
        released,manifest,archive,_=self.wasm_fixture();path=released/'wasm/build-info.json';info=json.loads(path.read_text());record=info['artifacts'][1]
        record['sourceFiles'].pop();record['sourceFingerprint']=hashlib.sha256(json.dumps(record['sourceFiles'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest();path.write_text(json.dumps(info))
        with self.assertRaisesRegex(ps1.checker.AuditError,'omitted a source/build input'):
            ps1.checker.audit_wasm(released,manifest,self.helper.root,archive,self.helper.inventory)

    def test_raw_receipt_cannot_claim_a_different_format(self):
        released,manifest,archive,directory=self.wasm_fixture();info=json.loads((directory/'build-info.json').read_text());info['artifacts'][0]['format']='emscripten-es-module'
        for root in [directory,released/'wasm']:(root/'build-info.json').write_text(json.dumps(info))
        with patch.object(package_release,'ROOT',self.helper.root),self.assertRaisesRegex(ValueError,'build format'):
            package_release.wasm_payload(directory,archive,{},self.helper.inventory)
        with self.assertRaisesRegex(ps1.checker.AuditError,'build format'):
            ps1.checker.audit_wasm(released,manifest,self.helper.root,archive,self.helper.inventory)

    def test_rust_native_is_enabled_only_for_explicit_or_full_build(self):
        h=self.helper
        for enabled in [False,True]:
            build=h.helper.work/('build-'+str(enabled))
            with patch.object(ps1.checker,'command') as run,patch.object(ps1.checker,'audit_native_file_api',return_value={}) as audit:
                ps1.checker.prepare_native_build(h.root,build,{},enable_sid8580=enabled)
            self.assertIn('-DTETORICA_ENABLE_SID8580='+('ON' if enabled else 'OFF'),run.call_args.args[0])
            self.assertEqual(audit.call_args.kwargs['enable_sid8580'],enabled)

    def test_sid_fixture_uses_resolved_executable_and_checks_its_existence(self):
        h=self.helper
        for identifier in ['sid','sid8580']:
            target=f'tetorica_{identifier}_fixture';fixture=h.helper.work/(target+'.exe');fixture.write_bytes(b'fixture')
            with patch.object(ps1.checker,'prepare_native_build',return_value={target:fixture}) as prepare,patch.object(ps1.checker,'command') as run:
                ps1.checker.build_sid_fixture(h.root,h.helper.work/'build',{},identifier)
            self.assertEqual(prepare.call_args.kwargs['enable_sid8580'],identifier=='sid8580')
            self.assertEqual(run.call_args.args[0],[fixture,'--self-test'])
            fixture.unlink()
            with patch.object(ps1.checker,'prepare_native_build',return_value={target:fixture}),patch.object(ps1.checker,'command'),self.assertRaisesRegex(ps1.checker.AuditError,'was not built'):
                ps1.checker.build_sid_fixture(h.root,h.helper.work/'build',{},identifier)

    def test_plain_audit_never_starts_rust_or_any_native_build(self):
        h=self.helper
        args=argparse.Namespace(source_zip=h.helper.work/'source.zip',wasm_zip=None,work_dir=h.helper.work/'plain-audit',audit_only=True,
            wasm_smoke=False,javascript_smoke=False,build_wasm=None,pokey_native_parity=False,ps1_native_parity=False,
            scsp_native_parity=False,application_audio_parity=False,sid_native_parity=False,sid8580_native_parity=False)
        source=h.helper.work/'tetorica-soundchip-native-0.1.6'
        with patch.object(ps1.checker.argparse.ArgumentParser,'parse_args',return_value=args),patch.object(ps1.checker,'unpack',return_value=source),patch.object(ps1.checker,'audit_manifest',return_value={'name':'tetorica-soundchip-native','version':'0.1.6'}),patch.object(ps1.checker,'audit_catalog',return_value=(h.catalog,h.inventory)),patch.object(ps1.checker,'audit_local_sources'),patch.object(ps1.checker,'command') as run,patch.object(ps1.checker,'build_sid_fixture') as build:
            ps1.checker.main()
        run.assert_not_called();build.assert_not_called()

    def test_sid_only_wasm_smoke_selects_its_fixture_without_legacy_ym2612_probe(self):
        h=self.helper
        for identifier in ['sid','sid8580']:
            args=argparse.Namespace(source_zip=h.helper.work/'source.zip',wasm_zip=h.helper.work/'wasm.zip',work_dir=h.helper.work/('smoke-'+identifier),audit_only=True,
                wasm_smoke=True,javascript_smoke=False,build_wasm=None,pokey_native_parity=False,ps1_native_parity=False,
                scsp_native_parity=False,application_audio_parity=False,sid_native_parity=False,sid8580_native_parity=False)
            source=h.helper.work/'tetorica-soundchip-native-0.1.6';wasm=h.helper.work/'wasm';fixture=h.helper.work/(identifier+'.exe');fixture.write_bytes(b'fixture')
            manifest={'name':'tetorica-soundchip-native','version':'0.1.6','artifacts':[identifier]}
            with patch.object(ps1.checker.argparse.ArgumentParser,'parse_args',return_value=args),patch.object(ps1.checker,'unpack',side_effect=[source,wasm]),patch.object(ps1.checker,'audit_manifest',return_value=manifest),patch.object(ps1.checker,'audit_catalog',return_value=(h.catalog,h.inventory)),patch.object(ps1.checker,'audit_local_sources'),patch.object(ps1.checker,'audit_wasm'),patch.object(ps1.checker,'build_sid_fixture',return_value={f'tetorica_{identifier}_fixture':fixture}) as build,patch.object(ps1.checker,'command') as run,patch.object(ps1.checker.shutil,'which',return_value='/fixture/node'):
                ps1.checker.main()
            self.assertEqual(build.call_args.args[-1],identifier)
            self.assertEqual(run.call_args_list[0].args[0],['node',source/f'tests/{identifier}_wasm_smoke.mjs','--wasm-dir',wasm/'wasm','--native-fixture',fixture])
            self.assertEqual(len(run.call_args_list),1)

    def test_sid_parity_flags_reject_unrelated_wasm_without_starting_a_compiler(self):
        h=self.helper
        for identifier in ['sid','sid8580']:
            args=argparse.Namespace(source_zip=h.helper.work/'source.zip',wasm_zip=None,work_dir=h.helper.work/('admission-'+identifier),
                audit_only=True,wasm_smoke=False,javascript_smoke=False,build_wasm=None,pokey_native_parity=False,ps1_native_parity=False,
                scsp_native_parity=False,application_audio_parity=False,sid_native_parity=identifier=='sid',sid8580_native_parity=identifier=='sid8580')
            source=h.helper.work/'tetorica-soundchip-native-0.1.6'
            with patch.object(ps1.checker.argparse.ArgumentParser,'parse_args',return_value=args),patch.object(ps1.checker,'unpack',return_value=source),patch.object(ps1.checker,'audit_manifest',return_value={'name':'tetorica-soundchip-native','version':'0.1.6'}),patch.object(ps1.checker,'audit_catalog',return_value=(h.catalog,h.inventory)),patch.object(ps1.checker,'audit_local_sources'),patch.object(ps1.checker,'command') as run,self.assertRaisesRegex(ps1.checker.AuditError,'needs supplied or rebuilt'):
                ps1.checker.main()
            run.assert_not_called()


if __name__=='__main__':unittest.main()
