"""Run with python3 -B -m unittest discover -s tests -v."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


class StaticStandalone(unittest.TestCase):
    def test_isolated_install_and_export(self):
        with tempfile.TemporaryDirectory(prefix='wechat-static-') as temporary:
            work = Path(temporary)
            skill = work / 'skills' / 'wechat-sticker'
            shutil.copytree(ROOT / 'skills/wechat-static-sticker', skill,
                            ignore=shutil.ignore_patterns('__pycache__', '.venv'))
            self.assertIn('name: wechat-sticker\n', (skill / 'SKILL.md').read_text())
            self.assertNotIn('<repo-root>', (skill / 'SKILL.md').read_text())
            for required in ('LICENSE', 'NOTICE.md', 'scripts/requirements.txt'):
                self.assertTrue((skill / required).is_file())
            for script in ('export_wechat.py', 'extract_sticker_sheet.py', 'package_sticker_pack.py'):
                result = subprocess.run([sys.executable, '-B', str(skill / 'scripts' / script), '--help'],
                                        cwd=work, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

            source = work / 'source'
            source.mkdir()
            artwork = Image.new('RGBA', (512, 512))
            ImageDraw.Draw(artwork).ellipse((80, 80, 430, 430), fill=(230, 140, 20, 255))
            artwork.save(source / 'art.png')
            Image.new('RGB', (750, 400), '#456789').save(source / 'banner.png')
            assets = [{'role': 'main', 'path': 'art.png', 'meaning': word}
                      for word in ('你好', '再见', '谢谢', '开心', '晚安', '早安', '加油', '收到')]
            assets += [{'role': role, 'path': 'art.png'} for role in ('cover', 'icon')]
            assets += [{'role': 'banner', 'path': 'banner.png'}]
            manifest = source / 'manifest.json'
            manifest.write_text(json.dumps({'mode': 'album', 'album_name': '测试表情', 'assets': assets}))
            output = work / 'delivery'

            def export(destination):
                return subprocess.run([sys.executable, '-B', str(skill / 'scripts/export_wechat.py'),
                                       '--manifest', str(manifest), '--output', str(destination)],
                                      cwd=work, capture_output=True, text=True)

            result = export(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / 'checks.json').read_text())
            self.assertEqual(len(report['files']), 11)
            for item in report['files']:
                with Image.open(output / item['file']) as image:
                    self.assertEqual(list(image.size), item['size'])
                    self.assertFalse(getattr(image, 'is_animated', False))
                    if item['role'] != 'banner':
                        self.assertLess(image.convert('RGBA').getchannel('A').getextrema()[0], 255)
            with zipfile.ZipFile(output / 'upload.zip') as archive:
                expected = {item['file'] for item in report['files']}
                expected.update(('checks.json', 'submission.json', '状态说明.txt'))
                self.assertEqual(set(archive.namelist()), expected)
                self.assertIsNone(archive.testzip())

            before = hashlib.sha256((output / 'upload.zip').read_bytes()).hexdigest()
            self.assertNotEqual(export(output).returncode, 0)
            self.assertEqual(before, hashlib.sha256((output / 'upload.zip').read_bytes()).hexdigest())
            assets[1]['meaning'] = assets[0]['meaning']
            manifest.write_text(json.dumps({'mode': 'album', 'assets': assets}))
            self.assertNotEqual(export(work / 'invalid').returncode, 0)
            self.assertFalse((work / 'invalid').exists())

            Image.new('RGB', (32, 32), 'red').save(source / 'animated.gif', save_all=True,
                append_images=[Image.new('RGB', (32, 32), 'blue')], duration=100, loop=0)
            manifest.write_text(json.dumps({'mode': 'assets', 'assets': [
                {'role': 'main', 'path': 'animated.gif', 'meaning': '你好'}]}))
            result = export(work / 'animated-output')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Animated input unsupported', result.stderr)
            self.assertFalse((work / 'animated-output').exists())


if __name__ == '__main__':
    unittest.main()
