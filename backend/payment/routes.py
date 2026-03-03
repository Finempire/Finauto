"""Payment / Razorpay routes."""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from backend.models import activate_user_payment

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/create-order', methods=['POST'])
@login_required
def create_order():
    try:
        import razorpay
        key_id = current_app.config['RAZORPAY_KEY_ID']
        key_secret = current_app.config['RAZORPAY_KEY_SECRET']

        if key_id == 'YOUR_KEY_ID_HERE':
            return jsonify({'success': False, 'message': 'Payment gateway not configured'}), 500

        client = razorpay.Client(auth=(key_id, key_secret))
        order = client.order.create({
            'amount': 29900,  # ₹299 in paise
            'currency': 'INR',
            'receipt': f'order_{current_user.email}',
            'payment_capture': 1,
        })
        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': key_id,
        })
    except ImportError:
        return jsonify({'success': False, 'message': 'Payment module not installed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating order: {str(e)}'}), 500


@payment_bp.route('/verify', methods=['POST'])
@login_required
def verify_payment():
    try:
        import razorpay
        import hmac
        import hashlib

        data = request.get_json()
        order_id = data.get('razorpay_order_id', '')
        payment_id = data.get('razorpay_payment_id', '')
        signature = data.get('razorpay_signature', '')

        key_secret = current_app.config['RAZORPAY_KEY_SECRET']
        message = f'{order_id}|{payment_id}'
        generated_signature = hmac.new(
            key_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        if generated_signature == signature:
            activate_user_payment(current_user.email)
            return jsonify({'success': True, 'message': 'Payment verified! 30-day access activated.'})
        else:
            return jsonify({'success': False, 'message': 'Payment verification failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Verification error: {str(e)}'}), 500
