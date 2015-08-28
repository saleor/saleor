var SORT_INFO = [ { name: 'id', dir: 'asc'}];

class DataTable extends React.Component {
    state = {
        data: this.props.data
    };

    handleSortChange(sortInfo) {
        SORT_INFO = sortInfo;

        this.setState({data: sort(this.props.data)});
    };

    handleColumnOrderChange(index, dropIndex) {
        var col = columns[index];
        columns.splice(index, 1); //delete from index, 1 item
        columns.splice(dropIndex, 0, col);
        this.setState({})
    };

    render() {
        return <DataGrid
            idProperty={this.props.columns[0]}
            dataSource={this.state.data}
            columns={this.props.columns}
            sortInfo={SORT_INFO}
            onSortChange={this.handleSortChange.bind(this)}
            onColumnOrderChange={this.handleColumnOrderChange.bind(this)}
            />;
    };
}

$(".data-table").each(function() {
    var columns = [];
    var data = [];

    $(this).find("thead").find("th").each(function(i) {
        columns[i] = {
            name: getColumnName(i, this.innerText),
            render: function(el) {
                return <div dangerouslySetInnerHTML={{__html: el}} />;
            }
        };
    });

    $(this).find("tbody").find("tr").each(function(i) {
        data[i] = {};
        $(this).find("td").each(function(j) {
            data[i][columns[j].name] = $(this).html();
        });
    });

    data = sort(data);

    var props = {
        columns: columns,
        data: data
    };
    React.render(<DataTable {...props} />, this.parentElement);
});

function sort(arr){
    return arr;//sorty(SORT_INFO, arr);
}

function getColumnName(index, name) {
    var spacer = " ";
    for (var i = 0; i < index; i++) {
        spacer += " ";
    }
    if (name) {
        return name;
    } else if (index) {
        return spacer;
    } else {
        return "id";
    }
}
