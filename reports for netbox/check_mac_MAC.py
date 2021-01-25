from dcim.choices import DeviceStatusChoices
from dcim.models import Device
from extras.reports import Report
from extras.models import CustomField
import re
# Отчет для Нетбокса.

def check_is_mac(mac):
    if mac is None:
        return False

    mac_mask = re.compile(r'\.|\-|\:')
    raw_mac = re.sub(mac_mask, '', mac).lower()
    result = re.match("^[0-9a-f]{12}$", raw_mac)

    if not result:
        return False
    else:
        return True
# Проверяет, заполнено ли кастомное поле P_MAC и проверяет МАК ли там.

class DevicePMACReport(Report):
    description = "Check that every device has either an MAC address assigned"
    def test_mac_address(self):
        for device in Device.objects.filter(status=DeviceStatusChoices.STATUS_ACTIVE):
            if mac:= device.cf.get('P_MAC'):
                if check_is_mac(mac):
                    self.log_success(device)
                else:
                    self.log_warning(device, f"Device has no valid MAC address: {mac}")
            else:
                self.log_failure(device, "Device has no MAC address")


class DeviceMACReport(Report):
    description = "Check that every device has either an MAC address assigned"
    def test_mac_address(self):
        for device in Device.objects.filter(status=DeviceStatusChoices.STATUS_ACTIVE):
            if mac:= device.cf.get('MAC'):
                if check_is_mac(mac):
                    self.log_success(device)
                else:
                    self.log_warning(device, f"Device has no valid MAC address: {mac}")
            else:
                self.log_failure(device, "Device has no MAC address")