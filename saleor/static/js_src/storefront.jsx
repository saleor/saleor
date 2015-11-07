class CartItemAmount extends React.Component {

    constructor() {
        super(...arguments);
        this.state = {
            error: null,
            lastSavedValue: this.props.value,
            renderSelect: false,
            renderSubmit: false,
            result: null,
            sending: false,
            value: this.props.value
        };
    }

    componentDidMount() {
        if (this.state.value < this.props.thresholdValue) {
            this.setState({renderSelect: true});
        }
    }

    change(event){
        let newValue = event.target.value;
        this.setState({result: null});
        if (newValue != this.props.thresholdValue || !this.state.renderSelect) {
            this.setState({value: newValue});
        }
        if (newValue >= this.props.thresholdValue) {
            this.setState({renderSelect: false});
        }
        if (newValue < this.props.thresholdValue && this.state.renderSelect) {
            this.sendQuantity(newValue);
        }

        if (!this.state.renderSelect && !this.state.sending) {
            this.setState({renderSubmit: true});
        }
    }

    valueChanged() {
        return this.state.lastSavedValue != this.state.value;
    }

    checkKey(event) {
        if (event.key == "Enter" && this.valueChanged()) {
            this.sendQuantityWrapper();
        }
    }

    sendQuantityWrapper() {
        this.sendQuantity(this.refs.inputQuantity.props.value);
    }

    sendQuantity(quantity) {
        this.setState({renderSubmit: false});
        this.setState({sending: true});

        $.ajax({
            url: this.props.url,
            method: "post",
            data: {quantity: quantity},
            complete: () => {
                this.setState({sending: false});
                if (quantity < this.props.thresholdValue) {
                    this.setState({renderSelect: true});
                }
            },
            success: (response) => {
                if (!quantity) {
                    if (!response.total) {
                        location.reload();
                    }
                    $(React.findDOMNode(this)).parents("tr").fadeOut(function() {
                        $(this).remove();
                    });
                }
                this.setState({result: "success", lastSavedValue: quantity});
                setTimeout(() => {
                    this.setState({result: null});
                }, 1000);
            },
            error: (response) => {
                this.setState({error: response.responseJSON.error.quantity, result: "error"});
            }
        });
    }

    removeFromCart() {
        this.sendQuantity(0);
    }

    render() {
        let classNames = React.addons.classSet({
            [this.props.className]: true,
            "has-success": this.state.result == "success",
            "has-error": this.state.result == "error"
        });

        let select = <select onChange={this.change.bind(this)} value={this.state.value} className="form-control cart-item-quantity-select">
                {this.props.options.map((option) =>
                    <CartItemAmountOption key={option} value={option} label={option == this.props.thresholdValue ? option+" +" : option} />)}
            </select>;

        let classNamesInput = React.addons.classSet({
            "input-group": true,
            "cart-item-quantity": true,
            "no-submit": (!this.state.renderSubmit || !this.valueChanged()) && !(this.state.result == "error")
        });
        let input =
            <div className={classNamesInput}>
                <input onKeyUp={this.checkKey.bind(this)} onChange={this.change.bind(this)} id="id_quantity" max={this.props.max} min="1" ref="inputQuantity"
                       name="quantity" type="number" value={this.state.value} />
                <span className="input-group-btn">
                    <button onClick={this.sendQuantityWrapper.bind(this)} className="btn btn-info" type="submit">Update</button>
                </span>
            </div>;
        return <div className={classNames}>
            {this.state.renderSelect ? select : input}
            {this.state.sending && !(this.state.result == "error")? <i className="fa fa-circle-o-notch fa-spin"></i> : ""}
            {this.state.result == "error" ? <span className="error text-danger">{this.state.error}</span> : ""}
            <button type="submit" className="btn btn-link btn-sm cart-item-remove" onClick={this.removeFromCart.bind(this)}>
                <span className="text-muted">Remove from cart</span>
            </button>
        </div>;
    }
}

class CartItemAmountOption extends React.Component {
    render() {
        var value = this.props.value;
        var label = this.props.label ? this.props.label : value;
        return <option value={value}>{label}</option>;
    };
}

class CartItemSubtotal extends React.Component {
    constructor() {
        super(...arguments);
        this.state = {
            value: this.props.value
        };
    }

    render() {
        return <span>{this.state.value}</span>;
    }
}

class CartTotal extends React.Component {
    constructor() {
        super(...arguments);
        this.state = {
            value: this.props.value
        };
    }

    render() {
        return <b>{this.state.value}</b>;
    }
}

var textInput = [];
var options = [1,2,3,4,5,6,7,8,9,10];
var csrftoken = $.cookie('csrftoken');
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(".cart-item-amount").each(function(index) {
    var $input = $(this).find("input");
    var $button = $(this).find("button");
    var value = $input.val();
    var name = $input.attr("name");
    var max = $input.attr("max");
    var props = {
        className: "",
        index: index,
        max: max,
        options: options.slice(0, max),
        thresholdValue: options[options.length - 1],
        url: $(this).find("form").attr("action"),
        value: value
    };

    $(this).find(".cart-item-quantity").removeClass("js-hidden");
    $button.addClass("invisible");
    textInput.push(this.firstElementChild);

    React.render(<CartItemAmount {...props} />, this);
});

var $cartTotal = $(".cart-total");
var cartTotalValue = $cartTotal.text();
if ($cartTotal.length) {
    var cartTotal = React.render(<CartTotal value={cartTotalValue}/>, $(".cart-total")[0]);
}

var cartSubtotals = [];
$(".cart-item-subtotal").each(function() {
    var productId = $(this).data("product-id");
    var props = {
        productId: productId,
        value: $(this).text()
    };
    cartSubtotals[productId] = React.render(<CartItemSubtotal {...props} />, this);
});

$(document).on("ajaxComplete", function(event, response) {
    var json = response.responseJSON;
    if (json.product_id && $cartTotal.length) {
        cartSubtotals[json.product_id].setState({value: json.subtotal});
        cartTotal.setState({value: json.total});
    }
});

class FormShippingToggler extends React.Component {
    constructor() {
        super(...arguments);
        this.state = {
            value: true
        };
    }

    componentDidMount() {
        $(".form-full").hide();
    }

    formFullToggle() {
        this.setState({value: event.target.checked});
        $(".form-full").toggle();
    }

    render() {
        return <div className="checkbox">
            <label>
                <input checked={this.state.value} type="checkbox" onChange={::this.formFullToggle} name="shipping_same_as_billing" />
                {this.props.label}
            </label>
        </div>;
    }
}

var $formFullToggle = $("#form-full-toggle");
if ($formFullToggle.length) {
    React.render(<FormShippingToggler label={$formFullToggle.data("label")} />, document.getElementById("form-full-toggle"));
}
