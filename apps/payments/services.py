import hashlib
import hmac
from django.conf import settings


class PaymentService:
    @staticmethod
    def create_razorpay_order(order):
        """Creates a Razorpay order. Amount is in paise (multiply by 100)."""
        import razorpay
        amount_paise = int(order.total * 100)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rz_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': order.order_number,
            'notes': {'order_number': order.order_number}
        })
        return rz_order

    @staticmethod
    def verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """HMAC SHA256 verification of Razorpay payment signature."""
        body = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, razorpay_signature)
