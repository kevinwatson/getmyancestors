#!/usr/bin/env python3
"""
   mergemyancestors.py - Merge GEDCOM data from FamilySearch Tree
   Copyright (C) 2014-2016 Giulio Genovese (giulio.genovese@gmail.com)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Written by Giulio Genovese <giulio.genovese@gmail.com>
   and by Benoît Fontaine <benoitfontaine.ba@gmail.com>
"""

from __future__ import print_function

# global import
import os
import sys
import argparse

# local import
from getmyancestors import Indi, Fam, Tree, Name, Note, Fact, Source, Ordinance, list_notes, list_sources

sys.path.append(os.path.dirname(sys.argv[0]))


class Gedcom:

    def __init__(self, file):
        self.f = file
        self.num = None
        self.level = 0
        self.pointer = None
        self.tag = None
        self.data = None
        self.flag = False
        self.indi = dict()
        self.fam = dict()
        self.note = dict()
        self.sour = dict()
        self.__parse()
        self.__add_id()

    def __parse(self):
        while self.__get_line():
            if self.tag == 'INDI':
                self.num = int(self.pointer[2:len(self.pointer) - 1])
                self.indi[self.num] = Indi(num=self.num)
                self.__get_indi()
            elif self.tag == 'FAM':
                self.num = int(self.pointer[2:len(self.pointer) - 1])
                if self.num not in self.fam:
                    self.fam[self.num] = Fam(num=self.num)
                self.__get_fam()
            elif self.tag == 'NOTE':
                self.num = int(self.pointer[2:len(self.pointer) - 1])
                if self.num not in self.note:
                    self.note[self.num] = Note(num=self.num)
                self.__get_note()
            elif self.tag == 'SOUR':
                self.num = int(self.pointer[2:len(self.pointer) - 1])
                if self.num not in self.sour:
                    self.sour[self.num] = Source(num=self.num)
                self.__get_source()
            else:
                continue

    def __get_line(self):
        # if the flag is set, skip reading a newline
        if self.flag:
            self.flag = False
            return True
        words = self.f.readline().split()

        if not words:
            return False
        self.level = int(words[0])
        if words[1][0] == '@':
            self.pointer = words[1]
            self.tag = words[2]
            self.data = ' '.join(words[3:])
        else:
            self.pointer = None
            self.tag = words[1]
            self.data = ' '.join(words[2:])
        return True

    def __get_indi(self):
        while self.f and self.__get_line() and self.level > 0:
            if self.tag == 'NAME':
                self.__get_name()
            elif self.tag == 'SEX':
                self.indi[self.num].gender = self.data
            elif self.tag == 'BIRT':
                self.__get_birt()
            elif self.tag == 'CHR':
                self.__get_chr()
            elif self.tag == 'DEAT':
                self.__get_deat()
            elif self.tag == 'BURI':
                self.__get_buri()
            elif self.tag == 'DSCR' or self.tag == 'OCCU' or self.tag == '_MILT':
                self.__get_fact()
            elif self.tag == 'BAPL':
                self.indi[self.num].baptism = self.__get_ordinance()
            elif self.tag == 'CONL':
                self.indi[self.num].confirmation = self.__get_ordinance()
            elif self.tag == 'ENDL':
                self.indi[self.num].endowment = self.__get_ordinance()
            elif self.tag == 'SLGC':
                self.indi[self.num].sealing_child = self.__get_ordinance()
            elif self.tag == 'FAMS':
                self.indi[self.num].fams_num.add(int(self.data[2:len(self.data) - 1]))
            elif self.tag == 'FAMC':
                self.indi[self.num].famc_num.add(int(self.data[2:len(self.data) - 1]))
            elif self.tag == '_FSFTID':
                self.indi[self.num].fid = self.data
            elif self.tag == 'NOTE':
                num = int(self.data[2:len(self.data) - 1])
                self.note[num] = Note(num=num)
                self.indi[self.num].notes.add(self.note[num])
            elif self.tag == 'SOUR':
                self.indi[self.num].sources.add(self.__get_link_source())
        self.flag = True

    def __get_fam(self):
        while self.__get_line() and self.level > 0:
            if self.tag == 'HUSB':
                self.fam[self.num].husb_num = int(self.data[2:len(self.data) - 1])
            elif self.tag == 'WIFE':
                self.fam[self.num].wife_num = int(self.data[2:len(self.data) - 1])
            elif self.tag == 'CHIL':
                self.fam[self.num].chil_num.add(int(self.data[2:len(self.data) - 1]))
            elif self.tag in ('MARR', 'DIV', 'ANUL', '_COML'):
                self.fam[self.num].marriage_facts.add(self.__get_marr())
            elif self.tag == 'SLGS':
                self.fam[self.num].sealing_spouse = self.__get_ordinance()
            elif self.tag == '_FSFTID':
                self.fam[self.num].fid = self.data
            elif self.tag == 'NOTE':
                num = int(self.data[2:len(self.data) - 1])
                self.note[num] = Note(num=num)
                self.fam[self.num].notes.add(self.note[num])
            elif self.tag == 'SOUR':
                self.fam[self.num].sources.add(self.__get_link_source())
        self.flag = True

    def __get_name(self):
        parts = self.data.split('/')
        name = Name()
        added = False
        name.given = parts[0].strip()
        name.surname = parts[1].strip()
        if parts[2]:
            name.suffix = parts[2]
        if not self.indi[self.num].name:
            self.indi[self.num].name = name
            added = True
        while self.__get_line() and self.level > 1:
            if self.tag == 'NPFX':
                name.prefix = self.data
            elif self.tag == 'TYPE':
                if self.data == 'aka':
                    self.indi[self.num].aka.add(name)
                    added = True
                elif self.data == 'married':
                    self.indi[self.num].married.add(name)
                    added = True
            elif self.tag == 'NICK':
                nick = Name()
                nick.given = self.data
                self.indi[self.num].nicknames.add(nick)
            elif self.tag == 'NOTE':
                num = int(self.data[2:len(self.data) - 1])
                self.note[num] = Note(num=num)
                name.note = self.note[num]
        if not added:
            self.indi[self.num].birthnames.add(name)
        self.flag = True

    def __get_birt(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].birtdate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].birtplac = self.data
        self.flag = True

    def __get_chr(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].chrdate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].chrplac = self.data
        self.flag = True

    def __get_deat(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].deatdate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].deatplac = self.data
        self.flag = True

    def __get_buri(self):
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                self.indi[self.num].buridate = self.data
            elif self.tag == 'PLAC':
                self.indi[self.num].buriplac = self.data
        self.flag = True

    def __get_marr(self):
        fact = Fact()
        if self.tag == 'MARR':
            fact.type = 'http://gedcomx.org/Marriage'
        elif self.tag == 'DIV':
            fact.type = 'http://gedcomx.org/Divorce'
        elif self.tag == 'ANUL':
            fact.type = 'http://gedcomx.org/Annulment'
        elif self.tag == '_COML':
            fact.type = 'http://gedcomx.org/CommonLawMarriage'
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                fact.date = self.data
            elif self.tag == 'PLAC':
                fact.place = self.data
            elif self.tag == 'NOTE':
                num = int(self.data[2:len(self.data) - 1])
                self.note[num] = Note(num=num)
                fact.note = (self.note[num])
        self.flag = True
        return fact

    def __get_fact(self):
        fact = Fact()
        fact.value = self.data
        if self.tag == 'DSCR':
            self.indi[self.num].physical_descriptions.add(fact)
        elif self.tag == 'OCCU':
            self.indi[self.num].occupations.add(fact)
        elif self.tag == '_MILT':
            self.indi[self.num].military.add(fact)
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                fact.date = self.data
            elif self.tag == 'PLAC':
                fact.place = self.data
            elif self.tag == 'NOTE':
                num = int(self.data[2:len(self.data) - 1])
                self.note[num] = Note(num=num)
                fact.note = (self.note[num])
        self.flag = True

    def __get_source(self):
        while self.__get_line() and self.level > 0:
            if self.tag == 'TITL':
                self.sour[self.num].title = self.data
            elif self.tag == 'AUTH':
                self.sour[self.num].citation = self.data
            elif self.tag == 'PUBL':
                self.sour[self.num].url = self.data
            elif self.tag == 'REFN':
                self.sour[self.num].fid = self.data
            elif self.tag == 'NOTE':
                num = int(self.data[2:len(self.data) - 1])
                self.note[num] = Note(num=num)
                self.sour[self.num].notes.add(self.note[num])
        self.flag = True

    def __get_link_source(self):
        num = int(self.data[2:len(self.data) - 1])
        if num not in self.sour:
            self.sour[num] = Source(num=num)
        page = None
        while self.__get_line() and self.level > 1:
            if self.tag == 'PAGE':
                page = self.data
            if self.tag == 'CONT':
                page += '\n' + self.data
        self.flag = True
        if page:
            return (self.sour[num], page)
        else:
            return (self.sour[num],)

    def __get_note(self):
        self.note[self.num].text = self.data
        while self.__get_line() and self.level > 0:
            if self.tag == 'CONT':
                self.note[self.num].text += '\n' + self.data
        self.flag = True

    def __get_ordinance(self):
        ordinance = Ordinance()
        while self.__get_line() and self.level > 1:
            if self.tag == 'DATE':
                ordinance.date = self.data
            elif self.tag == 'TEMP':
                ordinance.temple_code = self.data
            elif self.tag == 'STAT':
                ordinance.status = self.data
            elif self.tag == 'FAMC':
                num = int(self.data[2:len(self.data) - 1])
                if num not in self.fam:
                    self.fam[num] = Fam(num=num)
                ordinance.famc = self.fam[num]
        self.flag = True
        return ordinance

    def __add_id(self):
        for num in self.fam:
            if self.fam[num].husb_num:
                self.fam[num].husb_fid = self.indi[self.fam[num].husb_num].fid
            if self.fam[num].wife_num:
                self.fam[num].wife_fid = self.indi[self.fam[num].wife_num].fid
            for chil in self.fam[num].chil_num:
                self.fam[num].chil_fid.add(self.indi[chil].fid)
        for num in self.indi:
            for famc in self.indi[num].famc_num:
                self.indi[num].famc_fid.add((self.fam[famc].husb_fid, self.fam[famc].wife_fid))
            for fams in self.indi[num].fams_num:
                self.indi[num].fams_fid.add((self.fam[fams].husb_fid, self.fam[fams].wife_fid))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge GEDCOM data from FamilySearch Tree (4 Jul 2016)', add_help=False, usage='mergemyancestors.py -i input1.ged input2.ged ... [options]')
    try:
        parser.add_argument('-i', metavar='<FILE>', nargs='+', type=argparse.FileType('r', encoding='UTF-8'), default=sys.stdin, help='input GEDCOM files [stdin]')
        parser.add_argument('-o', metavar='<FILE>', nargs='?', type=argparse.FileType('w', encoding='UTF-8'), default=sys.stdout, help='output GEDCOM files [stdout]')
    except TypeError:
        sys.stderr.write('Python >= 3.4 is required to run this script\n')
        sys.stderr.write('(see https://docs.python.org/3/whatsnew/3.4.html#argparse)\n')
        exit(2)

    # extract arguments from the command line
    try:
        parser.error = parser.exit
        args = parser.parse_args()
    except SystemExit:
        parser.print_help()
        exit(2)

    tree = Tree()

    indi_counter = 0
    fam_counter = 0
    note_counter = 0
    temp_note = None

    # read the GEDCOM data
    for file in args.i:
        ged = Gedcom(file)

        # add informations about individuals
        for num in ged.indi:
            fid = ged.indi[num].fid
            if fid not in tree.indi:
                indi_counter += 1
                tree.indi[fid] = Indi(num=indi_counter)
                tree.indi[fid].fid = ged.indi[num].fid
            tree.indi[fid].fams_fid |= ged.indi[num].fams_fid
            tree.indi[fid].famc_fid |= ged.indi[num].famc_fid
            tree.indi[fid].name = ged.indi[num].name
            tree.indi[fid].birthnames = ged.indi[num].birthnames
            tree.indi[fid].nicknames = ged.indi[num].nicknames
            tree.indi[fid].aka = ged.indi[num].aka
            tree.indi[fid].married = ged.indi[num].married
            tree.indi[fid].gender = ged.indi[num].gender
            tree.indi[fid].birtdate = ged.indi[num].birtdate
            tree.indi[fid].birtplac = ged.indi[num].birtplac
            tree.indi[fid].chrdate = ged.indi[num].chrdate
            tree.indi[fid].chrplac = ged.indi[num].chrplac
            tree.indi[fid].deatdate = ged.indi[num].deatdate
            tree.indi[fid].deatplac = ged.indi[num].deatplac
            tree.indi[fid].buridate = ged.indi[num].buridate
            tree.indi[fid].buriplac = ged.indi[num].buriplac
            tree.indi[fid].physical_descriptions = ged.indi[num].physical_descriptions
            tree.indi[fid].occupations = ged.indi[num].occupations
            tree.indi[fid].military = ged.indi[num].military
            tree.indi[fid].notes = ged.indi[num].notes
            tree.indi[fid].sources = ged.indi[num].sources
            tree.indi[fid].baptism = ged.indi[num].baptism
            tree.indi[fid].confirmation = ged.indi[num].confirmation
            tree.indi[fid].endowment = ged.indi[num].endowment
            if not (tree.indi[fid].sealing_child and tree.indi[fid].sealing_child.famc):
                tree.indi[fid].sealing_child = ged.indi[num].sealing_child

        # add informations about families
        for num in ged.fam:
            husb, wife = (ged.fam[num].husb_fid, ged.fam[num].wife_fid)
            if (husb, wife) not in tree.fam:
                fam_counter += 1
                tree.fam[(husb, wife)] = Fam(husb, wife, fam_counter)
            tree.fam[(husb, wife)].chil_fid |= ged.fam[num].chil_fid
            tree.fam[(husb, wife)].fid = ged.fam[num].fid
            tree.fam[(husb, wife)].marriage_facts = ged.fam[num].marriage_facts
            tree.fam[(husb, wife)].notes = ged.fam[num].notes
            tree.fam[(husb, wife)].sources = ged.fam[num].sources
            tree.fam[(husb, wife)].sealing_spouse = ged.fam[num].sealing_spouse

    # merge notes by text
    list_notes = sorted(list_notes, key=lambda x: x.text)
    for i, n in enumerate(list_notes):
        if i == 0:
            n.num = 1
            continue
        if n.text == list_notes[i - 1].text:
            n.num = list_notes[i - 1].num
        else:
            n.num = list_notes[i - 1].num + 1

    # merge sources by fid
    list_sources = sorted(list_sources, key=lambda x: x.fid)
    for i, n in enumerate(list_sources):
        if i == 0:
            n.num = 1
            continue
        if n.fid == list_sources[i - 1].fid:
            n.num = list_sources[i - 1].num
        else:
            n.num = list_sources[i - 1].num + 1

    # compute number for family relationships and print GEDCOM file
    tree.reset_num()
    tree.print(args.o)
