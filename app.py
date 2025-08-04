from flask import Flask, render_template, request, jsonify, send_file
import os
import zipfile
import pikepdf
import tempfile
import shutil
from werkzeug.utils import secure_filename
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
# MODIFIED: Increased file size limit to 32MB
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to store cracking progress
cracking_status = {
    'is_running': False,
    'current_password': '',
    'total_attempts': 0,
    'found_password': None,
    'error': None,
    'unlocked_file_path': None
}

def cleanup_temp_files():
    """Clean up temporary files in temp_uploads folder"""
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Cleaned up: {filename}")
    except Exception as e:
        print(f"Error cleaning up files: {e}")

def cleanup_after_cracking():
    """Clean up files after cracking is complete"""
    # Wait a bit to ensure files are no longer in use
    time.sleep(2)
    cleanup_temp_files()

def is_numeric_password(password):
    """Check if password contains only digits"""
    return password.isdigit()

def try_zip_password(file_path, password):
    """Try to open ZIP file with given password"""
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Test if password works by trying to read the first file
            file_list = zip_file.namelist()
            if file_list:
                zip_file.read(file_list[0], pwd=password.encode('utf-8'))
            return True
    except:
        return False

def unlock_zip_file(file_path, password):
    """Remove password from ZIP file and return unlocked file path"""
    try:
        import tempfile
        import shutil
        
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            zip_file.extractall(path=temp_dir, pwd=password.encode('utf-8'))
        
        # Create new ZIP without password
        unlocked_path = file_path.replace('.zip', '_unlocked.zip')
        with zipfile.ZipFile(unlocked_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path_in_temp = os.path.join(root, file)
                    arcname = os.path.relpath(file_path_in_temp, temp_dir)
                    new_zip.write(file_path_in_temp, arcname)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        return unlocked_path
    except Exception as e:
        print(f"Error unlocking ZIP: {e}")
        return None

def try_pdf_password(file_path, password):
    """Try to open PDF file with given password"""
    try:
        with pikepdf.open(file_path, password=password) as pdf:
            # If we can open it, password is correct
            return True
    except:
        return False

def unlock_pdf_file(file_path, password):
    """Remove password from PDF file and return unlocked file path"""
    try:
        unlocked_path = file_path.replace('.pdf', '_unlocked.pdf')
        
        with pikepdf.open(file_path, password=password) as pdf:
            pdf.save(unlocked_path)
        
        return unlocked_path
    except Exception as e:
        print(f"Error unlocking PDF: {e}")
        return None

def try_7z_password(file_path, password):
    """Try to open 7Z file with given password"""
    try:
        import py7zr
        with py7zr.SevenZipFile(file_path, mode='r', password=password) as archive:
            # Test if password works by trying to list contents
            archive.list()
            return True
    except:
        return False

def unlock_7z_file(file_path, password):
    """Remove password from 7Z file and return unlocked file path"""
    try:
        import py7zr
        import tempfile
        import shutil
        
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        
        with py7zr.SevenZipFile(file_path, mode='r', password=password) as archive:
            archive.extractall(temp_dir)
        
        # Create new 7Z without password
        unlocked_path = file_path.replace('.7z', '_unlocked.7z')
        with py7zr.SevenZipFile(unlocked_path, mode='w') as new_archive:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path_in_temp = os.path.join(root, file)
                    arcname = os.path.relpath(file_path_in_temp, temp_dir)
                    new_archive.write(file_path_in_temp, arcname)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        return unlocked_path
    except Exception as e:
        print(f"Error unlocking 7Z: {e}")
        return None

def try_tar_password(file_path, password):
    """Try to open TAR file with given password"""
    try:
        import tarfile
        # TAR files typically don't have passwords, but some might be compressed
        with tarfile.open(file_path, 'r:*') as tar:
            tar.getmembers()
            return True
    except:
        return False

def unlock_tar_file(file_path, password):
    """Remove password from TAR file and return unlocked file path"""
    try:
        import tarfile
        # TAR files typically don't have passwords
        unlocked_path = file_path.replace('.tar', '_unlocked.tar')
        shutil.copy2(file_path, unlocked_path)
        return unlocked_path
    except Exception as e:
        print(f"Error unlocking TAR: {e}")
        return None

def try_rar_password(file_path, password):
    """Try to open RAR file with given password"""
    try:
        import rarfile
        with rarfile.RarFile(file_path, 'r', pwd=password.encode('utf-8')) as archive:
            # Test if password works by trying to list contents
            archive.namelist()
            return True
    except:
        return False

def unlock_rar_file(file_path, password):
    """Remove password from RAR file and return unlocked file path"""
    try:
        import rarfile
        import tempfile
        import shutil
        
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        
        with rarfile.RarFile(file_path, 'r', pwd=password.encode('utf-8')) as archive:
            archive.extractall(temp_dir)
        
        # Create new ZIP without password (RAR to ZIP conversion)
        unlocked_path = file_path.replace('.rar', '_unlocked.zip')
        with zipfile.ZipFile(unlocked_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path_in_temp = os.path.join(root, file)
                    arcname = os.path.relpath(file_path_in_temp, temp_dir)
                    new_zip.write(file_path_in_temp, arcname)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        return unlocked_path
    except Exception as e:
        print(f"Error unlocking RAR: {e}")
        return None

def crack_password(file_path, file_type, min_digits, max_digits, callback):
    """Main password cracking function with optimized performance and multi-threading"""
    global cracking_status
    
    cracking_status['is_running'] = True
    cracking_status['found_password'] = None
    cracking_status['error'] = None
    
    try:
        # Calculate total attempts
        total_attempts = 0
        for length in range(min_digits, max_digits + 1):
            total_attempts += 10 ** length
        
        cracking_status['total_attempts'] = total_attempts
        current_attempt = 0
        
        # Smart password patterns to try first (much faster)
        # These are the most commonly used numeric passwords
        smart_passwords = [
            # 4-digit passwords (most common)
            '0000', '1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999',
            '1234', '4321', '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009',
            '1110', '2220', '3330', '4440', '5550', '6660', '7770', '8880', '9990',
            '0123', '1230', '3210', '0987', '9876', '6789', '9870',
            '1000', '2000', '3000', '4000', '5000', '6000', '7000', '8000', '9000',
            '1999', '2001', '2020', '2021', '2022', '2023', '2024',
            '1212', '1313', '1414', '1515', '1616', '1717', '1818', '1919',
            '2121', '2323', '2424', '2525', '2626', '2727', '2828', '2929',
            '1122', '2233', '3344', '4455', '5566', '6677', '7788', '8899',
            '1100', '2200', '3300', '4400', '5500', '6600', '7700', '8800', '9900', '5656',
            
            # 5-digit passwords
            '00000', '11111', '12345', '54321', '00001', '00002', '00003', '00004', '00005',
            '10000', '20000', '30000', '40000', '50000', '60000', '70000', '80000', '90000',
            '12345', '54321', '11111', '22222', '33333', '44444', '55555',
            '66666', '77777', '88888', '99999', '00000',
            '12121', '13131', '14141', '15151', '16161', '17171', '18181', '19191',
            
            # 6-digit passwords
            '000000', '111111', '123456', '654321', '000001', '000002', '000003', '000004', '000005',
            '100000', '200000', '300000', '400000', '500000', '600000', '700000', '800000', '900000',
            '123456', '654321', '111111', '222222', '333333', '444444', '555555',
            '666666', '777777', '888888', '999999', '000000',
            '121212', '131313', '141414', '151515', '161616', '171717', '181818', '191919',
            
            # Date-based passwords (very common)
            '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999',
            '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009',
            '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019',
            '2020', '2021', '2022', '2023', '2024', '2025',
            
            # Common PIN patterns
            '0000', '1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999',
            '0123', '1234', '2345', '3456', '4567', '5678', '6789',
            '0987', '9876', '8765', '7654', '6543', '5432', '4321', '3210',
            
            # Sequential patterns
            '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009',
            '0010', '0020', '0030', '0040', '0050', '0060', '0070', '0080', '0090',
            '0100', '0200', '0300', '0400', '0500', '0600', '0700', '0800', '0900',
            '1000', '2000', '3000', '4000', '5000', '6000', '7000', '8000', '9000',
            
            # Repeating patterns
            '1010', '2020', '3030', '4040', '5050', '6060', '7070', '8080', '9090',
            '1100', '2200', '3300', '4400', '5500', '6600', '7700', '8800', '9900',
            '0011', '0022', '0033', '0044', '0055', '0066', '0077', '0088', '0099',
            
            # Common combinations
            '1234', '4321', '1111', '0000', '9999', '8888', '7777', '6666', '5555', '4444',
            '1212', '2121', '1313', '3131', '1414', '4141', '1515', '5151',
            '1122', '2233', '3344', '4455', '5566', '6677', '7788', '8899',
            '1100', '2200', '3300', '4400', '5500', '6600', '7700', '8800', '9900'
        ]
        
        # Filter smart passwords to match our range
        filtered_smart = [p for p in smart_passwords if min_digits <= len(p) <= max_digits]
        
        # Try smart passwords first (much faster)
        print(f"Trying {len(filtered_smart)} smart passwords first...")
        for password in filtered_smart:
            if not cracking_status['is_running']:
                return
            
            current_attempt += 1
            cracking_status['current_password'] = password
            
            # Try the password
            success = try_password(file_path, file_type, password)
            
            if success:
                cracking_status['found_password'] = password
                cracking_status['is_running'] = False
                
                # Create unlocked file
                unlocked_path = create_unlocked_file(file_path, file_type, password)
                if unlocked_path:
                    cracking_status['unlocked_file_path'] = unlocked_path
                
                return
            
            # Update progress every 10 attempts
            if current_attempt % 10 == 0 and callback:
                callback(current_attempt, total_attempts, password)
        
        # If smart passwords didn't work, try systematic approach with multi-threading
        print("Smart passwords failed, trying systematic approach with multi-threading...")
        
        # Use multi-threading for faster cracking
        max_workers = min(8, os.cpu_count() or 4)  # Use up to 8 threads
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Try passwords of different lengths
            for length in range(min_digits, max_digits + 1):
                if not cracking_status['is_running']:
                    return
                
                # Use more efficient password generation
                start_num = 10 ** (length - 1) if length > 1 else 0
                end_num = 10 ** length
                
                # Split work into chunks for multi-threading
                chunk_size = max(1000, (end_num - start_num) // max_workers)
                
                futures = []
                for chunk_start in range(start_num, end_num, chunk_size):
                    if not cracking_status['is_running']:
                        break
                    
                    chunk_end = min(chunk_start + chunk_size, end_num)
                    future = executor.submit(
                        crack_password_chunk, 
                        file_path, file_type, chunk_start, chunk_end, length
                    )
                    futures.append(future)
                
                # Check results as they complete
                for future in as_completed(futures):
                    if not cracking_status['is_running']:
                        return
                    
                    result = future.result()
                    if result:  # Password found
                        cracking_status['found_password'] = result
                        cracking_status['is_running'] = False
                        
                        # Create unlocked file
                        unlocked_path = create_unlocked_file(file_path, file_type, result)
                        if unlocked_path:
                            cracking_status['unlocked_file_path'] = unlocked_path
                        
                        return
                    
                    # Update progress
                    current_attempt += chunk_size
                    if current_attempt % 5000 == 0:
                        cracking_status['current_password'] = f"Batch {current_attempt // chunk_size}"
        
        # If we get here, no password was found
        cracking_status['is_running'] = False
        
        # Clean up temporary files after cracking is done
        cleanup_after_cracking()
        
    except Exception as e:
        cracking_status['error'] = str(e)
        cracking_status['is_running'] = False
        # Clean up even if there was an error
        cleanup_after_cracking()

def try_password(file_path, file_type, password):
    """Try password for any file type"""
    try:
        if file_type == 'zip':
            return try_zip_password(file_path, password)
        elif file_type == 'pdf':
            return try_pdf_password(file_path, password)
        elif file_type == '7z':
            return try_7z_password(file_path, password)
        elif file_type == 'tar':
            return try_tar_password(file_path, password)
        elif file_type == 'rar':
            return try_rar_password(file_path, password)
        return False
    except:
        return False

def create_unlocked_file(file_path, file_type, password):
    """Create unlocked file for any file type"""
    try:
        if file_type == 'zip':
            return unlock_zip_file(file_path, password)
        elif file_type == 'pdf':
            return unlock_pdf_file(file_path, password)
        elif file_type == '7z':
            return unlock_7z_file(file_path, password)
        elif file_type == 'tar':
            return unlock_tar_file(file_path, password)
        elif file_type == 'rar':
            return unlock_rar_file(file_path, password)
        return None
    except Exception as e:
        print(f"Error creating unlocked file: {e}")
        return None

def crack_password_chunk(file_path, file_type, start_num, end_num, length):
    """Crack passwords in a specific range (for multi-threading)"""
    for i in range(start_num, end_num):
        password = str(i).zfill(length)
        
        if try_password(file_path, file_type, password):
            return password
    
    return None

def crack_rockyou(file_path, file_type):
    """Crack password using RockYou dictionary"""
    global cracking_status
    
    cracking_status['is_running'] = True
    cracking_status['found_password'] = None
    cracking_status['error'] = None
    cracking_status['unlocked_file_path'] = None
    
    try:
        # Read passwords from rockyou.txt file
        rockyou_file_path = 'rockyou.txt'
        
        if not os.path.exists(rockyou_file_path):
            cracking_status['error'] = 'RockYou password file not found. Please ensure rockyou.txt is in the project directory.'
            cracking_status['is_running'] = False
            return
        
        # Read passwords from file
        with open(rockyou_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            rockyou_passwords = [line.strip() for line in f if line.strip()]
        
        cracking_status['total_attempts'] = len(rockyou_passwords)
        current_attempt = 0
        
        print(f"Loaded {len(rockyou_passwords)} passwords from RockYou file")
        
        for password in rockyou_passwords:
            if not cracking_status['is_running']:
                return
            
            current_attempt += 1
            cracking_status['current_password'] = password
            cracking_status['current_attempt'] = current_attempt
            
            # Try the password
            success = try_password(file_path, file_type, password)
            
            if success:
                cracking_status['found_password'] = password
                cracking_status['is_running'] = False
                
                # Create unlocked file
                unlocked_path = create_unlocked_file(file_path, file_type, password)
                if unlocked_path:
                    cracking_status['unlocked_file_path'] = unlocked_path
                
                return
        
        # If we get here, no password was found
        cracking_status['is_running'] = False
        
        # Clean up temporary files after cracking is done
        cleanup_after_cracking()
        
    except Exception as e:
        cracking_status['error'] = str(e)
        cracking_status['is_running'] = False
        # Clean up even if there was an error
        cleanup_after_cracking()

def crack_custom(file_path, file_type, custom_passwords):
    """Crack password using custom password list"""
    global cracking_status
    
    cracking_status['is_running'] = True
    cracking_status['found_password'] = None
    cracking_status['error'] = None
    cracking_status['unlocked_file_path'] = None
    
    try:
        cracking_status['total_attempts'] = len(custom_passwords)
        current_attempt = 0
        
        for password in custom_passwords:
            if not cracking_status['is_running']:
                return
            
            current_attempt += 1
            cracking_status['current_password'] = password
            cracking_status['current_attempt'] = current_attempt
            
            # Try the password
            success = try_password(file_path, file_type, password)
            
            if success:
                cracking_status['found_password'] = password
                cracking_status['is_running'] = False
                
                # Create unlocked file
                unlocked_path = create_unlocked_file(file_path, file_type, password)
                if unlocked_path:
                    cracking_status['unlocked_file_path'] = unlocked_path
                
                return
        
        # If we get here, no password was found
        cracking_status['is_running'] = False
        
        # Clean up temporary files after cracking is done
        cleanup_after_cracking()
        
    except Exception as e:
        cracking_status['error'] = str(e)
        cracking_status['is_running'] = False
        # Clean up even if there was an error
        cleanup_after_cracking()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/numerical')
def numerical():
    """Numerical password cracking page"""
    return render_template('numerical.html')

@app.route('/rockyou')
def rockyou():
    """RockYou password cracking page"""
    return render_template('rockyou.html')

@app.route('/custom')
def custom():
    """Custom password list page"""
    return render_template('custom.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start numerical password cracking"""
    global cracking_status
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get password range
    min_digits = int(request.form.get('min_digits', 4))
    max_digits = int(request.form.get('max_digits', 6))
    
    # MODIFIED: Updated the validation for the new range
    if min_digits < 0 or max_digits > 10 or min_digits > max_digits:
        return jsonify({'error': 'Invalid password range. Must be between 0 and 10.'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Determine file type
    file_ext = filename.lower().split('.')[-1]
    supported_types = {
        'zip': 'zip',
        'pdf': 'pdf',
        '7z': '7z',
        'tar': 'tar',
        'rar': 'rar'
    }
    
    if file_ext in supported_types:
        file_type = supported_types[file_ext]
    else:
        os.remove(file_path)
        return jsonify({'error': f'Unsupported file type: {file_ext}. Supported types: ZIP, PDF, 7Z, TAR, RAR'}), 400
    
    # Start password cracking in a separate thread
    def progress_callback(current, total, password):
        # This will be called to update progress
        pass
    
    thread = threading.Thread(
        target=crack_password,
        args=(file_path, file_type, min_digits, max_digits, progress_callback)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Numerical password cracking started',
        'filename': filename,
        'file_type': file_type,
        'min_digits': min_digits,
        'max_digits': max_digits
    })

@app.route('/upload_rockyou', methods=['POST'])
def upload_rockyou():
    """Handle file upload and start RockYou dictionary attack"""
    global cracking_status
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Determine file type
    file_ext = filename.lower().split('.')[-1]
    supported_types = {
        'zip': 'zip',
        'pdf': 'pdf',
        '7z': '7z',
        'tar': 'tar',
        'rar': 'rar'
    }
    
    if file_ext in supported_types:
        file_type = supported_types[file_ext]
    else:
        os.remove(file_path)
        return jsonify({'error': f'Unsupported file type: {file_ext}. Supported types: ZIP, PDF, 7Z, TAR, RAR'}), 400
    
    # Start RockYou dictionary attack
    thread = threading.Thread(
        target=crack_rockyou,
        args=(file_path, file_type)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'RockYou dictionary attack started',
        'filename': filename,
        'file_type': file_type
    })

@app.route('/upload_custom', methods=['POST'])
def upload_custom():
    """Handle file upload and start custom password attack"""
    global cracking_status
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Determine file type
    file_ext = filename.lower().split('.')[-1]
    supported_types = {
        'zip': 'zip',
        'pdf': 'pdf',
        '7z': '7z',
        'tar': 'tar',
        'rar': 'rar'
    }
    
    if file_ext in supported_types:
        file_type = supported_types[file_ext]
    else:
        os.remove(file_path)
        return jsonify({'error': f'Unsupported file type: {file_ext}. Supported types: ZIP, PDF, 7Z, TAR, RAR'}), 400
    
    # Get custom passwords
    custom_passwords = []
    if 'password_file' in request.files:
        # Handle uploaded password file
        password_file = request.files['password_file']
        password_content = password_file.read().decode('utf-8')
        custom_passwords = [line.strip() for line in password_content.split('\n') if line.strip()]
    elif 'custom_passwords' in request.form:
        # Handle custom passwords from textarea
        custom_passwords = json.loads(request.form['custom_passwords'])
    
    if not custom_passwords:
        return jsonify({'error': 'No passwords provided'}), 400
    
    # Start custom password attack
    thread = threading.Thread(
        target=crack_custom,
        args=(file_path, file_type, custom_passwords)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Custom password attack started',
        'filename': filename,
        'file_type': file_type,
        'password_count': len(custom_passwords)
    })

@app.route('/status')
def get_status():
    """Get current cracking status"""
    global cracking_status
    
    status = {
        'is_running': cracking_status['is_running'],
        'current_password': cracking_status['current_password'],
        'total_attempts': cracking_status['total_attempts'],
        'found_password': cracking_status['found_password'],
        'error': cracking_status['error'],
        'unlocked_file_path': cracking_status['unlocked_file_path']
    }
    
    return jsonify(status)

@app.route('/stop')
def stop_cracking():
    """Stop the password cracking process"""
    global cracking_status
    cracking_status['is_running'] = False
    return jsonify({'message': 'Cracking stopped'})

@app.route('/download/<filename>')
def download_file(filename):
    """Download the original file"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/download_unlocked/<path:filename>')
def download_unlocked_file(filename):
    """Download the unlocked file"""
    # Use os.path.basename() to get only the filename
    # This also makes the endpoint more secure by preventing path traversal.
    base_filename = secure_filename(os.path.basename(filename))
    
    # Construct the correct and safe file path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], base_filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'Unlocked file not found'}), 404

@app.route('/get_unlocked_filename')
def get_unlocked_filename():
    """Get the filename of the unlocked file"""
    global cracking_status
    if cracking_status['unlocked_file_path']:
        filename = os.path.basename(cracking_status['unlocked_file_path'])
        return jsonify({'filename': filename})
    else:
        return jsonify({'error': 'No unlocked file available'}), 404

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up temporary files"""
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return jsonify({'message': 'Files cleaned up successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Clean up any existing temporary files on startup
    cleanup_temp_files()
    print("Starting Password Cracker Pro...")
    print("Clean up completed. Ready to serve!")
    app.run(debug=True, host='0.0.0.0', port=5000)