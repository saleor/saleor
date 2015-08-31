import React from "react";
import DataGrid from "react-datagrid";
import sorty from "sorty";

class DataTable extends React.Component {
    state = {
        data: sort(this.props.data, this.props.sortInfo),
        sortInfo: this.props.sortInfo
    };

    handleSortChange(sortInfo) {
        this.setState({
            sortInfo: sortInfo,
            data: sort(this.state.data, sortInfo)
        });
    };

    render() {
        return <DataGrid
            idProperty={this.props.columns[0]+""}
            dataSource={this.state.data}
            columns={this.props.columns}
            sortInfo={this.state.sortInfo}
            onSortChange={this.handleSortChange.bind(this)}
            />;
    };
}

$(".data-table-sortable").each(function() {
    var columns = [];
    var data = [];

    $(this).find("thead").find("th").each(function(i) {
        var that = this;
        columns[i] = {
            name: getColumnName(i, this.innerText),
            render: function(el) {
                return <span dangerouslySetInnerHTML={{__html: el}} />;
            },
            textAlign: $(this).hasClass("right-align") ? "right" : "left"
        };
    });

    $(this).find("tbody").find("tr").each(function(i) {
        data[i] = {};
        $(this).find("td").each(function(j) {
            data[i][columns[j].name] = $(this).html();
        });
    });

    var sort = $(this).data("sort") ? $(this).data("sort") : "ID";
    var sortDir = $(this).data("sort-dir") ? $(this).data("sort-dir") : "desc";
    var props = {
        columns: columns,
        data: data,
        sortInfo: [{ name: sort, dir: sortDir}],
    };
    React.render(<DataTable {...props} />, this.parentElement);
});

function sort(arr, sortInfo){
    return sorty(sortInfo, arr);
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
    }
}
