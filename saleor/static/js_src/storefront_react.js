var CartItemAmount = React.createClass({
    getInitialState: function() {
        return {
            value: this.props.value
        }
    },
    change: function(event){
        if (event.target.value == this.lastOptionValue) {
            var parent = this.getDOMNode().parentNode;
            React.unmountComponentAtNode(parent);
            parent.appendChild(textInput[this.props.name]);
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
        return <select name={this.props.name} onChange={this.change} value={this.state.value} className="form-control">
            {this.props.options.map(function(option) {
                return <CartItemAmountOption key={option} value={option} label={option == that.lastOptionValue ? option+" +" : option} />
            })}
        </select>;
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
    var $submit = $(this).find("button");
    var value = $input.val();
    var name = $input.attr("name");
    var hasErrors = $(this).hasClass("has-error");
    textInput[name] = this;

    var options = [1,2,3,4,5,6,7,8,9,10];

    if (options.indexOf(parseInt(value)) != -1 && !hasErrors) {
        React.render(<CartItemAmount options={options} value={value} name={name}/>, this.parentNode);
    }
});
