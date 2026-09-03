import os

base_dir = '/home/vaibhav/.gemini/antigravity/scratch/ecommerce-platform/templates'

templates = {
    'orders/checkout.html': """{% extends 'base.html' %}
{% block content %}
<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">Checkout</h1>
    <div class="flex flex-col md:flex-row gap-8">
        <div class="w-full md:w-2/3">
            <h2 class="text-xl font-semibold mb-2">Select Address</h2>
            <form id="checkout-form" method="post" action="{% url 'orders:checkout' %}">
                {% csrf_token %}
                <div class="space-y-4">
                    {% for address in addresses %}
                    <div class="border p-4 rounded">
                        <label class="flex items-center space-x-2">
                            <input type="radio" name="address_id" value="{{ address.id }}" required class="form-radio">
                            <span>
                                <strong>{{ address.full_name }}</strong><br>
                                {{ address.address_line_1 }}<br>
                                {{ address.city }}, {{ address.state }} - {{ address.pincode }}
                            </span>
                        </label>
                    </div>
                    {% endfor %}
                    <div class="border p-4 rounded">
                        <label class="flex items-center space-x-2">
                            <input type="radio" name="new_address" value="true" class="form-radio" id="new-address-radio">
                            <span>Use a new address</span>
                        </label>
                        <div id="new-address-form" class="hidden mt-4 space-y-2">
                            <input type="text" name="full_name" placeholder="Full Name" class="w-full border p-2">
                            <input type="text" name="phone" placeholder="Phone" class="w-full border p-2">
                            <input type="text" name="address_line_1" placeholder="Address Line 1" class="w-full border p-2">
                            <input type="text" name="address_line_2" placeholder="Address Line 2" class="w-full border p-2">
                            <input type="text" name="city" placeholder="City" class="w-full border p-2">
                            <input type="text" name="state" placeholder="State" class="w-full border p-2">
                            <input type="text" name="pincode" placeholder="Pincode" class="w-full border p-2">
                        </div>
                    </div>
                </div>
                <input type="hidden" name="coupon_code" id="form_coupon_code" value="">

                <h2 class="text-xl font-semibold mt-8 mb-2">Payment Method</h2>
                <div class="space-y-2">
                    <label class="flex items-center space-x-2">
                        <input type="radio" name="payment_method" value="razorpay" required checked class="form-radio">
                        <span>Razorpay (Card / UPI / Netbanking)</span>
                    </label>
                    <label class="flex items-center space-x-2">
                        <input type="radio" name="payment_method" value="cod" required class="form-radio">
                        <span>Cash on Delivery</span>
                    </label>
                </div>
                <button type="submit" class="mt-6 bg-blue-600 text-white px-6 py-2 rounded">Place Order</button>
            </form>
        </div>

        <div class="w-full md:w-1/3">
            <div class="border p-4 rounded bg-gray-50">
                <h2 class="text-xl font-semibold mb-4">Order Summary</h2>
                {% for item in cart.items.all %}
                <div class="flex justify-between mb-2">
                    <span>{{ item.quantity }}x {{ item.variant.product.name }}</span>
                    <span>₹{{ item.line_total }}</span>
                </div>
                {% endfor %}
                <hr class="my-4">
                <div class="flex justify-between mb-2">
                    <span>Subtotal</span>
                    <span>₹<span id="summary-subtotal">{{ subtotal }}</span></span>
                </div>
                <div class="flex justify-between mb-2">
                    <span>Shipping</span>
                    <span>₹{{ shipping_cost }}</span>
                </div>
                <div class="flex justify-between mb-2 text-green-600 hidden" id="discount-row">
                    <span>Discount</span>
                    <span>-₹<span id="summary-discount">0.00</span></span>
                </div>
                <hr class="my-4">
                <div class="flex justify-between font-bold text-lg mb-4">
                    <span>Total</span>
                    <span>₹<span id="summary-total">{{ total }}</span></span>
                </div>

                <div class="flex space-x-2">
                    <input type="text" id="coupon_input" placeholder="Coupon Code" class="w-full border p-2 rounded">
                    <button type="button" id="apply_coupon_btn" class="bg-gray-800 text-white px-4 py-2 rounded">Apply</button>
                </div>
                <p id="coupon-message" class="text-sm mt-2"></p>
            </div>
        </div>
    </div>
</div>

<script>
    document.getElementById('new-address-radio').addEventListener('change', function() {
        document.getElementById('new-address-form').classList.remove('hidden');
    });

    document.querySelectorAll('input[name="address_id"]').forEach(el => {
        el.addEventListener('change', function() {
            document.getElementById('new-address-form').classList.add('hidden');
        });
    });

    document.getElementById('apply_coupon_btn').addEventListener('click', function() {
        const code = document.getElementById('coupon_input').value;
        const subtotal = parseFloat(document.getElementById('summary-subtotal').innerText);

        fetch("{% url 'orders:apply_coupon' %}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({ coupon_code: code, subtotal: subtotal })
        })
        .then(response => response.json())
        .then(data => {
            const msgEl = document.getElementById('coupon-message');
            if (data.success) {
                msgEl.innerText = data.message;
                msgEl.className = 'text-sm mt-2 text-green-600';
                document.getElementById('form_coupon_code').value = code;

                document.getElementById('discount-row').classList.remove('hidden');
                document.getElementById('summary-discount').innerText = data.discount_amount.toFixed(2);

                const shipping = parseFloat("{{ shipping_cost }}");
                const newTotal = subtotal + shipping - data.discount_amount;
                document.getElementById('summary-total').innerText = newTotal.toFixed(2);
            } else {
                msgEl.innerText = data.message;
                msgEl.className = 'text-sm mt-2 text-red-600';
            }
        });
    });

    // Update form action based on payment method
    document.getElementById('checkout-form').addEventListener('submit', function(e) {
        const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
        // In this implementation checkout view processes cart to order, then redirects to confirm.
        // Actually we don't need to change action here. Order confirm view handles the rest.
    });
</script>
{% endblock %}""",
    'orders/order_confirm.html': """{% extends 'base.html' %}
{% block content %}
<div class="container mx-auto p-4 max-w-lg">
    <h1 class="text-2xl font-bold mb-4">Confirm Your Order</h1>
    <div class="border p-4 rounded mb-4">
        <h2 class="text-lg font-semibold mb-2">Order #{{ order.order_number }}</h2>
        <div class="flex justify-between mb-1">
            <span>Subtotal:</span>
            <span>₹{{ order.subtotal }}</span>
        </div>
        <div class="flex justify-between mb-1">
            <span>Shipping:</span>
            <span>₹{{ order.shipping_cost }}</span>
        </div>
        {% if order.discount_amount > 0 %}
        <div class="flex justify-between mb-1 text-green-600">
            <span>Discount:</span>
            <span>-₹{{ order.discount_amount }}</span>
        </div>
        {% endif %}
        <hr class="my-2">
        <div class="flex justify-between font-bold text-xl">
            <span>Total:</span>
            <span>₹{{ order.total }}</span>
        </div>
    </div>

    <button id="rzp-button1" class="w-full bg-blue-600 text-white py-3 rounded font-semibold text-lg">Pay Now with Razorpay</button>
    <a href="{% url 'payments:cod_place_order' order.order_number %}" class="block text-center mt-4 text-gray-600 underline">Or Place as Cash on Delivery</a>

    <form name='razorpayform' action="{% url 'payments:payment_callback' %}" method="POST">
        {% csrf_token %}
        <input type="hidden" name="razorpay_payment_id" id="razorpay_payment_id">
        <input type="hidden" name="razorpay_order_id" id="razorpay_order_id" value="{{ razorpay_order_id }}">
        <input type="hidden" name="razorpay_signature"  id="razorpay_signature" >
        <input type="hidden" name="order_number" value="{{ order.order_number }}">
    </form>
</div>

<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
<script>
var options = {
    "key": "{{ razorpay_key_id }}",
    "amount": "{{ amount }}",
    "currency": "INR",
    "name": "Your Store Name",
    "description": "Order #{{ order.order_number }}",
    "order_id": "{{ razorpay_order_id }}",
    "handler": function (response){
        document.getElementById('razorpay_payment_id').value = response.razorpay_payment_id;
        document.getElementById('razorpay_signature').value = response.razorpay_signature;
        document.razorpayform.submit();
    },
    "prefill": {
        "name": "{{ order.shipping_name }}",
        "email": "{{ request.user.email }}",
        "contact": "{{ order.shipping_phone }}"
    },
    "theme": {
        "color": "#3399cc"
    }
};
var rzp1 = new Razorpay(options);
rzp1.on('payment.failed', function (response){
        alert(response.error.description);
});
document.getElementById('rzp-button1').onclick = function(e){
    rzp1.open();
    e.preventDefault();
}
</script>
{% endblock %}""",
    'orders/order_list.html': """{% extends 'base.html' %}
{% block content %}
<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold mb-4">Your Orders</h1>
    <div class="space-y-4">
        {% for order in orders %}
        <div class="border p-4 rounded flex justify-between items-center">
            <div>
                <a href="{% url 'orders:order_detail' order.order_number %}" class="text-lg font-semibold text-blue-600 hover:underline">Order #{{ order.order_number }}</a>
                <p class="text-sm text-gray-500">{{ order.created_at|date:"M d, Y" }}</p>
                <p class="font-medium mt-1">Total: ₹{{ order.total }}</p>
            </div>
            <div>
                <span class="px-3 py-1 rounded-full text-sm font-medium
                    {% if order.status == 'pending' %}bg-yellow-100 text-yellow-800
                    {% elif order.status == 'cancelled' %}bg-red-100 text-red-800
                    {% elif order.status == 'delivered' %}bg-green-100 text-green-800
                    {% else %}bg-blue-100 text-blue-800{% endif %}">
                    {{ order.get_status_display }}
                </span>
            </div>
        </div>
        {% empty %}
        <p>You have no orders yet.</p>
        {% endfor %}
    </div>
</div>
{% endblock %}""",
    'orders/order_detail.html': """{% extends 'base.html' %}
{% block content %}
<div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">Order #{{ order.order_number }}</h1>
        <span class="px-4 py-2 rounded-full font-semibold
            {% if order.status == 'pending' %}bg-yellow-100 text-yellow-800
            {% elif order.status == 'cancelled' %}bg-red-100 text-red-800
            {% elif order.status == 'delivered' %}bg-green-100 text-green-800
            {% else %}bg-blue-100 text-blue-800{% endif %}">
            {{ order.get_status_display }}
        </span>
    </div>

    <!-- Timeline -->
    <div class="mb-8 p-4 bg-gray-50 rounded">
        <h3 class="font-semibold mb-2">Status Timeline</h3>
        <p>Ordered: {{ order.created_at|date:"M d, Y H:i" }}</p>
        <!-- Additional timeline steps can be added based on Shipment model -->
    </div>

    <div class="flex flex-col md:flex-row gap-8">
        <div class="w-full md:w-2/3">
            <h2 class="text-xl font-semibold mb-4">Items</h2>
            <div class="border rounded divide-y">
                {% for item in order.items.all %}
                <div class="p-4 flex justify-between">
                    <div>
                        <p class="font-medium">{{ item.product_name }}</p>
                        {% if item.variant_info %}
                        <p class="text-sm text-gray-500">{{ item.variant_info }}</p>
                        {% endif %}
                        <p class="text-sm text-gray-500">Qty: {{ item.quantity }}</p>
                    </div>
                    <div class="font-medium">₹{{ item.line_total }}</div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="w-full md:w-1/3 space-y-6">
            <div class="border p-4 rounded">
                <h2 class="text-lg font-semibold mb-2">Summary</h2>
                <div class="flex justify-between mb-1"><span>Subtotal:</span><span>₹{{ order.subtotal }}</span></div>
                <div class="flex justify-between mb-1"><span>Shipping:</span><span>₹{{ order.shipping_cost }}</span></div>
                <div class="flex justify-between mb-1 text-green-600"><span>Discount:</span><span>-₹{{ order.discount_amount }}</span></div>
                <hr class="my-2">
                <div class="flex justify-between font-bold text-xl"><span>Total:</span><span>₹{{ order.total }}</span></div>
            </div>

            <div class="border p-4 rounded">
                <h2 class="text-lg font-semibold mb-2">Shipping Details</h2>
                <p><strong>{{ order.shipping_name }}</strong></p>
                <p>{{ order.shipping_phone }}</p>
                <p>{{ order.shipping_address_line_1 }}</p>
                {% if order.shipping_address_line_2 %}<p>{{ order.shipping_address_line_2 }}</p>{% endif %}
                <p>{{ order.shipping_city }}, {{ order.shipping_state }} - {{ order.shipping_pincode }}</p>
                <p>{{ order.shipping_country }}</p>
            </div>

            <div class="border p-4 rounded">
                <h2 class="text-lg font-semibold mb-2">Payment Info</h2>
                {% for payment in order.payments.all %}
                <p class="text-sm">Gateway: {{ payment.get_gateway_display }}</p>
                <p class="text-sm">Status: {{ payment.get_status_display }}</p>
                {% if payment.transaction_id %}<p class="text-sm text-gray-500">Txn ID: {{ payment.transaction_id }}</p>{% endif %}
                {% empty %}
                <p class="text-sm">No payment records found.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}""",
    'payments/payment_success.html': """{% extends 'base.html' %}
{% block content %}
<div class="container mx-auto p-4 text-center mt-12">
    <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 text-green-600 mb-4">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
    </div>
    <h1 class="text-3xl font-bold mb-2">Payment Successful!</h1>
    <p class="text-gray-600 mb-6">Your order #{{ order.order_number }} has been confirmed.</p>
    <a href="{% url 'orders:order_detail' order.order_number %}" class="bg-blue-600 text-white px-6 py-2 rounded">View Order Detail</a>
</div>
{% endblock %}""",
    'payments/payment_failed.html': """{% extends 'base.html' %}
{% block content %}
<div class="container mx-auto p-4 text-center mt-12">
    <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-600 mb-4">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
    </div>
    <h1 class="text-3xl font-bold mb-2">Payment Failed</h1>
    <p class="text-gray-600 mb-6">Unfortunately, your payment could not be processed for order #{{ order.order_number }}.</p>
    <a href="{% url 'orders:checkout' %}" class="bg-blue-600 text-white px-6 py-2 rounded">Try Again</a>
</div>
{% endblock %}""",
    'payments/cod_confirm.html': """{% extends 'base.html' %}
{% block content %}
<div class="container mx-auto p-4 max-w-md text-center mt-12">
    <h1 class="text-2xl font-bold mb-4">Confirm COD Order</h1>
    <p class="mb-6">You have selected Cash on Delivery for Order #{{ order.order_number }}. The total amount to be paid on delivery is ₹{{ order.total }}.</p>
    <form action="{% url 'payments:cod_place_order' order.order_number %}" method="post">
        {% csrf_token %}
        <button type="submit" class="bg-green-600 text-white px-6 py-3 rounded font-semibold w-full">Confirm Order</button>
    </form>
</div>
{% endblock %}"""
}

for path, content in templates.items():
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)
print("Templates generated.")
