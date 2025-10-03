"""
@copyright: 2009 Bastian Blank <waldi@debian.org>
@license: GNU GPL-3
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct


class MalformedIfoHeaderError(Exception):
    pass


class VmgIfoHeader:
    _struct = struct.Struct('>12s I 12x IHI 24x H 32x Q 24x II 56x IIIIIIII 32x 1792x')

    def __init__(self, buf):
        data = self._struct.unpack(buf)

        (id,
         self.part_bup_end,
         self.part_ifo_end,
         version,
         category,
         self.number_titlesets,
         pos,
         vmgi_mat_end,
         fp_pgc_start,
         self.part_menu_vob_start,
         self.tt_srpt_start,
         self.vmgm_pgci_ut_start,
         self.vmgm3_start,
         self.vmgm4_start,
         self.vmgm5_start,
         self.vmgm6_start,
         self.vmgm7_start) = data

        if id != b'DVDVIDEO-VMG':
            raise MalformedIfoHeaderError


class VtsIfoHeader:
    _struct = struct.Struct('>12s I 12x IH 94x I 60x IIIIIIIIII 24x 1792x')

    def __init__(self, buf):
        data = self._struct.unpack(buf)

        (id,
         self.part_bup_end,
         self.part_ifo_end,
         self.version,
         self.vts_mat_end,
         self.part_menu_vob_start,
         self.part_title_vob_start,
         self.vts_ptt_srpt_start,
         self.vts_pgci_start,
         vtsm3_start,
         vtsm4_start,
         vtsm5_start,
         vtsm6_start,
         vtsm7_start,
         vtsm8_start,
         ) = data

        if id != b'DVDVIDEO-VTS':
            raise MalformedIfoHeaderError


class _Ifo:
    def dump(self):
        return self._file.dump(self.header.part_ifo_end + 1),

    
class VmgIfo(_Ifo):
    _struct_tt_srpt = struct.Struct('>h 2x I')
    _struct_title = struct.Struct('>cbHhbbI')

    def __init__(self, file):
        self._file = file

        self.header = VmgIfoHeader(self._file.read_sector(0))

    def tt_srpt(self) -> dict:
        """
        Get title information from TT_SRPT
        """
        buf = self._file.read_sector(self.header.tt_srpt_start)
        data = self._struct_tt_srpt.unpack(buf[:8])
        num_titles, end = data
        titles = []
        title_fields = ['title_type', 'angles', 'num_chapters', 'parental', 'vtsn', 'title_number', 'start_sector']
        for pos in range(8, end, 12):
            entry = buf[pos:pos + 12]
            data = self._struct_title.unpack(entry)
            titles.append(dict(zip(title_fields, data)))

        return {'title_count': num_titles, 'titles': titles}


class VtsIfo(_Ifo):
    _struct_vts_ptt_srpt = struct.Struct('>h 2x II')
    _struct_vts_pgci = struct.Struct('>hh')

    def __init__(self, file):
        self._file = file

        self.header = VtsIfoHeader(self._file.read_sector(0))

    def vts_ptt_srpt(self) -> dict:
        """
        Get title and chapter information from VTS_PTT_SRPT
        """
        buf = self._file.read_sector(self.header.vts_ptt_srpt_start)
        num_titles, end_address, first_offset = self._struct_vts_ptt_srpt.unpack(buf[:12])
        ptt = []
        num_chapters = {}
        for pos in range(first_offset, end_address, 4):
            # pgcn, pgn = struct.unpack('>hh', buf[pos:pos + 4])
            pgcn, pgn = self._struct_vts_pgci.unpack(buf[pos:pos + 4])
            ptt.append({'pgcn': pgcn, 'pgn': pgn})
            if pgcn not in num_chapters or pgn > num_chapters[pgcn]:
                num_chapters[pgcn] = pgn
        return {'titles': num_titles, 'chapters': num_chapters}
