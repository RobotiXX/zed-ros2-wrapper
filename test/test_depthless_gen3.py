"""Regression: depth NONE must still read explicit GEN_3 tracking parameters.

Source Humble and the built wrapper overlay before running. The deliberately
unavailable serial number prevents opening the attached camera. This checks
parameter initialization, not sensor acquisition or trajectory performance.
"""
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest


class DepthlessGen3Test(unittest.TestCase):
    def test_gen3_parameters_are_read_without_dense_depth(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            config = directory / 'params.yaml'
            config.write_text('''/**:
  ros__parameters:
    depth:
      depth_mode: NONE
    pos_tracking:
      pos_tracking_enabled: true
      pos_tracking_mode: GEN_3
''')
            path = directory / 'launch.log'
            with path.open('w') as log:
                process = subprocess.Popen([
                    'ros2', 'launch', 'zed_wrapper', 'zed_camera.launch.py',
                    'camera_model:=zed2i', 'camera_name:=depthless_regression',
                    'serial_number:=99999999', 'publish_tf:=false', 'publish_map_tf:=false',
                    'ros_params_override_path:=' + str(config)],
                    env=dict(os.environ, ROS_DOMAIN_ID='198', ROS_LOCALHOST_ONLY='1',
                             RCUTILS_COLORIZED_OUTPUT='0'),
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    deadline = time.monotonic() + 25
                    while time.monotonic() < deadline:
                        text = path.read_text(errors='replace')
                        if 'Positional tracking mode: GEN 3' in text:
                            break
                        if process.poll() is not None:
                            break
                        time.sleep(.1)
                    self.assertIn('Depth mode: NONE', text, text[-3000:])
                    self.assertIn('Positional tracking mode: GEN 3', text, text[-3000:])
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGINT)
                        try:
                            process.wait(timeout=12)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGTERM)
                            try:
                                process.wait(timeout=3)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGKILL)
                                process.wait(timeout=3)


if __name__ == '__main__':
    unittest.main()
