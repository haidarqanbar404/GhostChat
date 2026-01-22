class SteganographyEngine:
    ZERO = '\u200b' 
    ONE = '\u200c' 
    MARKER = '\u2060'

    @staticmethod
    def bytes_to_invisible(data: bytes) -> str:
        binary_string = ''.join(f'{byte:08b}' for byte in data)
        
        invisible_chars = []
        for bit in binary_string:
            if bit == '0':
                invisible_chars.append(SteganographyEngine.ZERO)
            else:
                invisible_chars.append(SteganographyEngine.ONE)
        
        return SteganographyEngine.MARKER + "".join(invisible_chars) + SteganographyEngine.MARKER

    @staticmethod
    def invisible_to_bytes(text: str) -> bytes:
        if text.count(SteganographyEngine.MARKER) < 2:
            raise ValueError("No hidden message markers found in text.")

        parts = text.split(SteganographyEngine.MARKER)
        hidden_segment = parts[1] 

        binary_string = []
        for char in hidden_segment:
            if char == SteganographyEngine.ZERO:
                binary_string.append('0')
            elif char == SteganographyEngine.ONE:
                binary_string.append('1')
            else:
                pass
        
        full_binary = "".join(binary_string)

        byte_array = bytearray()
        for i in range(0, len(full_binary), 8):
            byte = full_binary[i:i+8]
            if len(byte) == 8:
                byte_array.append(int(byte, 2))
                
        return bytes(byte_array)

    @staticmethod
    def contains_hidden_msg(text: str) -> bool:
        return text.count(SteganographyEngine.MARKER) >= 2