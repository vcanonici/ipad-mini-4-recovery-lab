import hashlib
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inspect_img4 import FormatError, inspect, parse
from prepare_nonce_allowlist import prepare

def der(tag, value):
    n=len(value); width=(n.bit_length()+7)//8
    return bytes([tag])+(bytes([n]) if n<128 else bytes([128+width])+n.to_bytes(width,'big'))+value

def seq(*parts): return der(0x30,b''.join(parts))
def text(value): return der(0x16,value)
def prop(name,value): return seq(text(name),der(4,value))
def image(seed=b'\x01\x02\x03\x04\x05\x06\x07\x08', nonce=None, restore=True, duplicate=False):
    nonce=hashlib.sha1(seed).digest() if nonce is None else nonce
    props=[prop(b'BNCH',nonce)]
    if duplicate: props.append(prop(b'BNCH',b'X'*20))
    manifest=seq(text(b'IM4M'),seq(*props))
    parts=[text(b'IMG4'),seq(text(b'IM4P'),text(b'illb'),text(b'synthetic'),der(4,b'not Apple firmware')),der(0xa0,manifest)]
    if restore: parts.append(der(0xa1,seq(text(b'IM4R'),seq(prop(b'BNCN',seed)))))
    return seq(*parts)

class InspectionTests(unittest.TestCase):
    def test_known_nonce_match_and_endianness(self):
        report,payload=inspect(image())
        self.assertTrue(report['nonce_relationship_matches'])
        self.assertEqual(report['generator_uint64_le'],'0x0807060504030201')
        self.assertFalse(report['signature_verified'])
        self.assertFalse(report['boot_verified'])
        self.assertTrue(payload)
    def test_wrong_ticket_nonce_is_rejected(self):
        report,_=inspect(image(nonce=b'X'*20))
        self.assertFalse(report['nonce_relationship_matches'])
    def test_missing_restore_info_is_not_a_nonce_pass(self):
        report,_=inspect(image(restore=False))
        self.assertIsNone(report['nonce_relationship_matches'])
    def test_duplicate_nonce_is_ambiguous(self):
        with self.assertRaises(FormatError): inspect(image(duplicate=True))
    def test_truncated_lengths_fail(self):
        for data in [b'',b'\x30',b'\x30\x82\x01',image()[:-1]]:
            with self.subTest(data=data[:8]):
                with self.assertRaises(FormatError): parse(data)
    def test_trailing_media_is_explicit(self):
        with self.assertRaises(FormatError): inspect(image()+b'\0'*8)
        report,_=inspect(image()+b'\0'*8,allow_trailing=True)
        self.assertEqual(report['trailing_bytes'],8)
    def test_indefinite_length_is_not_der(self):
        with self.assertRaises(FormatError): parse(b'\x30\x80\x00\x00')
    def test_wrong_image_type_fails(self):
        with self.assertRaises(FormatError): inspect(seq(text(b'OTHER')))
    def test_wrong_patcher_input_is_refused(self):
        with self.assertRaises(ValueError): prepare(b'wrong firmware')

if __name__=='__main__': unittest.main()
