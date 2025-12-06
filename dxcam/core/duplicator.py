import ctypes
from dataclasses import dataclass, InitVar
from dxcam._libs.d3d11 import *
from dxcam._libs.dxgi import *
from dxcam.core.device import Device
from dxcam.core.output import Output


@dataclass
class Duplicator:
    def __init__(self, output: Output, device: Device):
        self._output = output
        self._device = device
        self.duplicator = self._output.output.DuplicateOutput(device.im_context)
        self.texture = None
        self.updated = False

    def update_frame(self, force_update=False):
    try:
        self.updated = False
        hr, frame_info, resource = self.duplicator.AcquireNextFrame(100, None)
        if hr == 0:  # S_OK
            self.texture = self._device.im_context.CreateTexture2DFromDXGIResource(resource)
            self.updated = True
            return True
        elif hr == -1057209500:  # DXGI_ERROR_WAIT_TIMEOUT (no change)
            if force_update:
                self.duplicator.ReleaseFrame()  # Release any pending
                hr2, frame_info2, resource2 = self.duplicator.AcquireNextFrame(0, None)  # Timeout 0 for immediate
                if hr2 == 0 and resource2:
                    self.texture = self._device.im_context.CreateTexture2DFromDXGIResource(resource2)
                self.updated = True
                return True
            return False  # Skip as before
        else:
            self._output.update_desc()
            return False
    except comtypes.COMError:
        return False
    finally:
        if 'frame_info' in locals():
            self.duplicator.ReleaseFrame(frame_info)

    def release_frame(self):
        if self.texture:
            self.texture.Release()
            self.texture = None
        self.updated = False

    def release(self):
        if self.duplicator is not None:
            self.duplicator.Release()
            self.duplicator = None

    def __repr__(self) -> str:
        return "<{} Initalized:{}>".format(
            self.__class__.__name__,
            self.duplicator is not None,
        )
