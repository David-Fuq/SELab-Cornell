import uasyncio as asyncio
import struct
import json
import sys
from agbot_file_util import (
    serialize_json, serialize_csv, chunk_file, file_types,
    generate_header_message, generate_payload_message, generate_last_message,
    calcule_hash
)

class FileTransfer:
    def __init__(self):
        """Initialize the file transfer manager"""
        self.transfer_in_progress = False
        self.current_file = None
        self.current_file_type = None
        
    async def send_file(self, file_data, file_type, file_name=None):
        """
        Send a file asynchronously over serial connection.
        
        Args:
            file_data: The file data (dict for JSON, bytes/string for CSV)
            file_type: The file type ("JSON" or "CSV")
            file_name: Optional file name to include
            
        Returns:
            True if transfer was successful, False otherwise
        """
        if self.transfer_in_progress:
            print("A file transfer is already in progress")
            return False
            
        self.transfer_in_progress = True
        try:
            # Convert file data to the appropriate format
            file_type_id = file_types.get(file_type, None)
            if file_type_id is None:
                print("Invalid file type:", file_type)
                return False
                
            chunk_size = 100
            
            # Prepare file data
            if file_type == "JSON":
                file_encoded = serialize_json(file_data)
            elif file_type == "CSV":
                if isinstance(file_data, str):
                    file_encoded = bytearray(file_data, 'utf-8')
                else:
                    file_encoded = file_data
            else:
                print("Unsupported file type")
                return False
                
            # Chunk the file data
            file_chunks = chunk_file(file_encoded, chunk_size)
            
            # Send file header
            header_message = generate_header_message(len(file_chunks), file_encoded, file_type_id)
            await self._send_packet("FT,H", header_message.hex())
            await asyncio.sleep_ms(50)  # Give receiver time to process
            
            # Send file chunks
            for index, chunk in enumerate(file_chunks):
                payload_message = generate_payload_message(chunk, index)
                await self._send_packet("FT,P", f"{index},{len(file_chunks)},{payload_message.hex()}")
                # Short sleep to allow other tasks to run and not overwhelm the receiver
                await asyncio.sleep_ms(20)
                
            # Send last message
            last_message = generate_last_message(file_name)
            await self._send_packet("FT,L", last_message.hex())
            
            return True
            
        except Exception as e:
            print(f"Error in file transfer: {e}")
            return False
        finally:
            self.transfer_in_progress = False
            
    async def _send_packet(self, cmd, data):
        """Send a packet via the serial connection"""
        # The actual printing to stdout will be handled by the calling code
        sys.stdout.write(f"{cmd},{data}\n")
        
    async def receive_file(self, header_data):
        """
        Begin receiving a file from serial connection.
        
        Args:
            header_data: The hex-encoded header data
            
        Returns:
            None, but will print updates during transfer
        """
        try:
            # Process header
            header_bytes = bytes.fromhex(header_data)
            if not header_bytes or header_bytes[0] != 0x01:
                print("FT,ERR,Invalid header received")
                return False
                
            file_type_id = header_bytes[1]
            num_chunks = header_bytes[2]
            file_size = struct.unpack("<I", header_bytes[3:7])[0]
            file_checksum = header_bytes[7]
            
            print(f"FT,INFO,Starting file transfer: {num_chunks} chunks, {file_size} bytes")
            
            # Send acknowledgment for header
            print("FT,ACK,H")
            
            # Now we're ready to receive chunks
            return True
            
        except Exception as e:
            print(f"FT,ERR,{e}")
            return False
            
    async def process_chunk(self, chunk_index, total_chunks, chunk_data):
        """
        Process a received file chunk.
        
        Args:
            chunk_index: The index of this chunk
            total_chunks: Total number of chunks expected
            chunk_data: The hex-encoded chunk data
            
        Returns:
            True if chunk was processed correctly, False otherwise
        """
        try:
            chunk_bytes = bytes.fromhex(chunk_data)
            
            if not chunk_bytes or chunk_bytes[0] != 0x02:
                print("FT,ERR,Invalid chunk format")
                return False
                
            received_index = chunk_bytes[1]
            if received_index != int(chunk_index):
                print(f"FT,ERR,Chunk index mismatch: expected {chunk_index}, got {received_index}")
                return False
                
            # Here we would append the chunk data to our file buffer
            # For now we just acknowledge receipt
            print(f"FT,ACK,P,{chunk_index}")
            
            return True
            
        except Exception as e:
            print(f"FT,ERR,{e}")
            return False
            
    async def finalize_file(self, last_data, file_name=None):
        """
        Finalize file reception.
        
        Args:
            last_data: The hex-encoded last message
            file_name: Optional file name for saving
            
        Returns:
            True if file was successfully processed, False otherwise
        """
        try:
            last_bytes = bytes.fromhex(last_data)
            
            if not last_bytes or last_bytes[0] != 0x03:
                print("FT,ERR,Invalid end marker")
                return False
                
            # Here we would save the complete file
            print(f"FT,DONE,{file_name if file_name else 'unknown'}")
            
            return True
            
        except Exception as e:
            print(f"FT,ERR,{e}")
            return False