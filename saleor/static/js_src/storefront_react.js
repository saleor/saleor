var CartItemAmount = React.createClass({
    getInitialState: function() {
        return {
            value: this.props.value
        }
    },
    change: function(event){
        if (event.target.value == this.lastOptionValue) {
            var parent = this.getDOMNode().parentNode;
            console.log(parent.innerHTML);
            React.unmountComponentAtNode(parent);
            parent.appendChild(inputs[this.props.name]);
        } else {
            this.setState({value: event.target.value});
        }
    },
    render: function() {
        this.lastOptionValue = _.clone(this.props.options).pop() + 1;
        this.lastOptionLabel = this.lastOptionValue + " +";
        return <select name={this.props.name} onChange={this.change} value={this.state.value} className="form-control">
            {this.props.options.map(function(option) {
                return <CartItemAmountOption key={option} value={option} />
            })}
            <CartItemAmountLastOption value={this.lastOptionValue} label={this.lastOptionLabel} />
        </select>;
    }
});

class CartItemAmountOption extends React.Component {
    render() {
        return <option value={this.props.value}>{this.props.value}</option>;
    };
}

class CartItemAmountLastOption extends React.Component {
    render() {
        return <option value={this.props.value}>{this.props.label}</option>;
    };
}

var inputs = [];
$(".cart-item-quantity").each(function() {
    var input = $(this).find("input");
    var value = input.val();
    var name = input.attr("name");
    inputs[name] = input[0];

    React.render(<CartItemAmount options={_.range(1, 10)} value={value} name={name} />, this);
});
