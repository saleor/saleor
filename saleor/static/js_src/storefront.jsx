var CartItemAmount = React.createClass({
    componentDidMount: function() {
        this.parent = this.getDOMNode().parentNode;
    },
    getInitialState: function() {
        return {
            value: this.props.value
        }
    },
    change: function(event){
        if (event.target.value == this.lastOptionValue) {
            React.unmountComponentAtNode(this.parent);
            this.parent.appendChild(textInput[this.props.name]);
        } else {
            this.setState({value: event.target.value});
            this.submitForm();
        }
    },
    submitForm: function() {
        $(".form-cart").submit();
    },
    render: function() {
        this.lastOptionValue = this.props.options[this.props.options.length - 1];
        var that = this;
        return <div className={this.props.className}>
            <select name={this.props.name} onChange={this.change} value={this.state.value} className="form-control cart-item-quantity-select">
                {this.props.options.map(function(option) {
                    return <CartItemAmountOption key={option} value={option} label={option == that.lastOptionValue ? option+" +" : option} />
                })}
            </select>
        </div>;
    }
});

class CartItemAmountOption extends React.Component {
    render() {
        var value = this.props.value;
        var label = this.props.label ? this.props.label : value;
        return <option value={value}>{label}</option>;
    };
}

var textInput = [];
$(".cart-item-quantity").each(function() {
    var $input = $(this).find("input");
    var $button = $(this).find("button");
    var value = $input.val();
    var name = $input.attr("name");
    var hasErrors = $(this).hasClass("has-error");

    var options = [1,2,3,4,5,6,7,8,9,10];

    if (options.indexOf(parseInt(value)) != -1 && !hasErrors) {
        React.render(<CartItemAmount options={options} value={value} name={name}/>, this.parentNode);
    }

    $(this).removeClass("hidden");
    $button.addClass("invisible");
    textInput[name] = this;
}).on("keyup change", function() {
    $(this).find("input").addClass("input-left");
    $(this).find("button").removeClass("invisible");
});

var FormShippingToggler = React.createClass({
    componentDidMount: function() {
        $(".form-full").hide();
    },
    getInitialState: function() {
        return {
            value: true
        }
    },
    formFullToggle: function() {
        this.setState({value: event.target.checked});
        $(".form-full").toggle();
    },
    render: function() {
        return <div className="checkbox">
            <label>
                <input checked={this.state.value} type="checkbox" onChange={this.formFullToggle} name="shipping_same_as_billing" />
                {this.props.label}
            </label>
        </div>;
    }
});

var $formFullToggle = $("#form-full-toggle");
if ($formFullToggle.length) {
    React.render(<FormShippingToggler label={$formFullToggle.data("label")} />, document.getElementById("form-full-toggle"));
}
