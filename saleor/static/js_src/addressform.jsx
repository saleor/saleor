/* @flow */

let LevelSelect = ({rules, id, label, name, value, autoComplete, onChange, required}) => {
  if (rules.hasOwnProperty('sub_keys') || rules.hasOwnProperty('sub_names')) {
    let codes = [], names = [], lnames = [];
    if (rules.hasOwnProperty('sub_keys')) {
      codes = rules.sub_keys.split('~');
    } else {
      codes = rules.sub_names.split('~');
    }
    if (rules.hasOwnProperty('sub_names')) {
      names = rules.sub_names.split('~');
    } else {
      names = rules.sub_keys.split('~');
    }
    if (rules.hasOwnProperty('sub_lnames')) {
      lnames = rules.sub_lnames.split('~');
    } else {
      lnames = codes.map(() => undefined);
    }
    let options = codes.map((code, i) => <option value={code} key={code}>{lnames[i] ? `${names[i]} (${lnames[i]})` : names[i]}</option>);
    return <div className="form-group">
      <label htmlFor={id}>{label}</label>
        <select id={id} name={name} className="form-control" value={value} autoComplete={autoComplete} onChange={onChange} required={required}>
        <option></option>
        {options}
      </select>
    </div>;
  }
  return <div className="form-group">
    <label htmlFor={id}>{label}</label>
    <input id={id} name={name} className="form-control" value={value} autoComplete={autoComplete} onChange={onChange} />
  </div>;
}

class AddressForm extends React.Component {
  constructor() {
    super(...arguments);
    let country = this.props.country;
    this.state = {address: {country}};
  }
  getRule(parts) {
    let rule = {}
    let key = parts.join('/');
    if (key in this.props.data) {
      rule = {...rule, ...this.props.data[key]};
    }
    key = `${key}--${this.props.lang}`
    if (key in this.props.data) {
      rule = {...rule, ...this.props.data[key]};
    }
    return rule;
  }
  getRules() {
    let rules = {
      fmt: '%N%n%O%n%A%n%Z %C',
      require: 'AC'
    };
    let {address} = this.state;
    if (address.hasOwnProperty('country')) {
      rules = {...rules, ...this.getRule([address.country])};
      if (rules.fmt.indexOf('%S') !== -1) {
        if (address.hasOwnProperty('level1')) {
          rules = {...rules, ...this.getRule([address.country, address.level1])};
          if (rules.fmt.indexOf('%C') !== -1) {
            if (address.hasOwnProperty('level2')) {
              rules = {...rules, ...this.getRule([address.country, address.level1, address.level2])};
            }
          }
        }
      } else {
        if (rules.fmt.indexOf('%C') !== -1) {
          if (address.hasOwnProperty('level2')) {
            rules = {...rules, ...this.getRule([address.country, address.level2])};
          }
        }
      }
    }
    return rules;
  }
  _renderAddressField(rules, required) {
    return <div className="row">
      <div className="col-xs-8">
        <div className="form-group">
          <label htmlFor="field-address1">Address</label>
        <input id="field-address1" className="form-control" name="street_address_1" autoComplete="address-line1" required={required} onChange={this._onAddress1Change.bind(this)} value={this.state.address.address1} />
        </div>
      </div>
      <div className="col-xs-4">
        <div className="form-group">
          <label htmlFor="field-address2">Address</label>
        <input id="field-address2" className="form-control" name="street_address_2" autoComplete="address-line2" onChange={this._onAddress2Change.bind(this)} value={this.state.address.address2} />
        </div>
      </div>
    </div>;
  }
  _renderCountryField(rules) {
    let options = this.props.countries.map((code) => {
      let countryRules = this.getRule([code]);
      return <option value={code} key={code}>{countryRules.name}</option>;
    });
    return <div className="form-group">
      <label htmlFor="field-country">Country/region</label>
    <select id="field-country" name="country" className="form-control" value={this.state.address.country} autoComplete="country" ref="country" onChange={this._onCountryChange.bind(this)} required={true}>
        {options}
      </select>
    </div>;
  }
  _renderLevel1Field(rules, required: boolean) {
    let label = 'Province';
    if (rules.hasOwnProperty('state_name_type')) {
      let map = {
        area: 'Area',
        county: 'County',
        department: 'Department',
        district: 'District',
        do_si: 'Do/Si',
        emirate: 'Emirate',
        island: 'Island',
        oblast: 'Oblast',
        parish: 'Parish',
        prefecture: 'Prefecture',
        state: 'State'
      }
      label = map[rules.state_name_type];
    }
    let countryRules = {};
    if (this.state.address.hasOwnProperty('country')) {
      let nodes = [this.state.address.country];
      countryRules = this.getRule(nodes);
    }
    return <LevelSelect rules={countryRules} id="field-level1" name="country_area" autoComplete="address-level1" onChange={this._onLevel1Change.bind(this)} label={label} value={this.state.address.level1} required={required} />;
  }
  _renderLevel2Field(rules, required: boolean) {
    let label = 'City';
    if (rules.hasOwnProperty('locality_name_type')) {
      let map = {
        district: 'District',
        post_town: 'Post town'
      }
      label = map[rules.locality_name_type];
    }
    let levelRules = {};
    if (rules.fmt.indexOf('%S') !== -1) {
      // we have a level1 field
      if (this.state.address.hasOwnProperty('level1')) {
        let nodes = [this.state.address.country, this.state.address.level1];
        levelRules = this.getRule(nodes);
      }
    } else {
      let nodes = [this.state.address.country];
      levelRules = this.getRule(nodes);
    }
    return <LevelSelect rules={levelRules} id="field-level2" name="city" autoComplete="address-level2" onChange={this._onLevel2Change.bind(this)} label={label} value={this.state.address.level2} required={required} />;
  }
  _renderLevel3Field(rules, required: boolean) {
    let label = 'Sublocality';
    if (rules.hasOwnProperty('sublocality_name_type')) {
      let map = {
        district: 'District',
        neighborhood: 'Neighborhood',
        village_township: 'Village/township'
      }
      label = map[rules.sublocality_name_type];
    }
    let levelRules = {};
    if (rules.fmt.indexOf('%S') !== -1) {
      if (this.state.address.hasOwnProperty('level1') && this.state.address.hasOwnProperty('level2')) {
        let nodes = [this.state.address.country, this.state.address.level1, this.state.address.level2];
        levelRules = this.getRule(nodes);
      }
    } else {
      if (this.state.address.hasOwnProperty('level2')) {
        let nodes = [this.state.address.country, this.state.address.level2];
        levelRules = this.getRule(nodes);
      }
    }
    return <LevelSelect rules={levelRules} id="field-level3" name="country_area_2" autoComplete="address-level3" onChange={this._onLevel3Change.bind(this)} label={label} value={this.state.address.level3} required={required} />;
  }
  _renderNameField(rules, required: boolean) {
    return <div className="row">
      <div className="col-xs-6">
        <div className="form-group">
          <label htmlFor="field-country">First name</label>
          <input className="form-control" name="first_name" autoComplete="given-name" required={required} onChange={this._onFirstNameChange.bind(this)} value={this.state.address.firstName} />
        </div>
      </div>
      <div className="col-xs-6">
        <div className="form-group">
          <label htmlFor="field-country">Last name</label>
          <input className="form-control" name="last_name" autoComplete="family-name" required={required} onChange={this._onLastNameChange.bind(this)} value={this.state.address.lastName} />
        </div>
      </div>
    </div>;
  }
  _renderOrganizationField(rules, required) {
    return <div className="form-group">
      <label htmlFor="field-country">Company/organization</label>
    <input className="form-control" name="company_name" autoComplete="organization" required={required} onChange={this._onOrganizationChange.bind(this)} value={this.state.address.organization} />
    </div>;
  }
  _renderPostcodeField(rules, required) {
    let label = 'Postal code';
    if (rules.hasOwnProperty('zip_name_type')) {
      let map = {
        pin: 'PIN',
        zip: 'ZIP code'
      }
      label = map[rules.zip_name_type];
    }
    let pattern;
    if (rules.hasOwnProperty('zip')) {
      pattern = rules.zip;
    }
    let hint;
    if (rules.hasOwnProperty('zipex')) {
      let examples = rules.zipex.split(',');
      hint = `Example: ${examples[0]}`;
    }
    if (rules.hasOwnProperty('postprefix')) {
      return <div className="form-group">
        <label htmlFor="field-country">{label}</label>
        <div className="input-group">
          <div className="input-group-addon">{rules.postprefix}</div>
          <input type="text" className="form-control" name="postal_code" autoComplete="postal-code" required={required} pattern={pattern} onChange={this._onPostcodeChange.bind(this)} value={this.state.address.postcode} />
        </div>
        {hint ? <span className="help-block">{hint}</span> : undefined}
      </div>;
    }
    return <div className="form-group">
      <label htmlFor="field-country">{label}</label>
      <input type="text" className="form-control" name="postcode" autoComplete="postal-code" required={required} pattern={pattern} onChange={this._onPostcodeChange.bind(this)} value={this.state.address.postcode} />
      {hint ? <span className="help-block">{hint}</span> : undefined}
    </div>;
  }
  _onCountryChange(event) {
    let country = event.target.value;
    let address = {...this.state.address, country};
    this.setState({address})
  }
  _onLevel1Change(event) {
    let level1 = event.target.value;
    let address = {...this.state.address, level1};
    this.setState({address})
  }
  _onLevel2Change(event) {
    let level2 = event.target.value;
    let address = {...this.state.address, level2};
    this.setState({address})
  }
  _onLevel3Change(event) {
    let level3 = event.target.value;
    let address = {...this.state.address, level3};
    this.setState({address})
  }
  _onFirstNameChange(event) {
    let firstName = event.target.value;
    let address = {...this.state.address, firstName};
    this.setState({address})
  }

  _onLastNameChange(event) {
    let lastName = event.target.value;
    let address = {...this.state.address, lastName};
    this.setState({address})
  }

  _onOrganizationChange(event) {
    let organization = event.target.value;
    let address = {...this.state.address, organization};
    this.setState({address})
  }
  _onPostcodeChange(event) {
    let postcode = event.target.value;
    let address = {...this.state.address, postcode};
    this.setState({address})
  }
  _onAddress1Change(event) {
    let address1 = event.target.value;
    let address = {...this.state.address, address1};
    this.setState({address})
  }
  _onAddress2Change(event) {
    let address2 = event.target.value;
    let address = {...this.state.address, address2};
    this.setState({address})
  }
  _renderControl(controlFormat, width, rules) {
    let control;
    let required = rules.require.indexOf(controlFormat) !== -1;
    switch (controlFormat) {
      case 'A':
        control = this._renderAddressField(rules, required);
        break;
      case 'C':
        control = this._renderLevel2Field(rules, required);
        break;
      case 'D':
        control = this._renderLevel3Field(rules, required);
        break;
      case 'N':
        control = this._renderNameField(rules, required);
        break;
      case 'O':
        control = this._renderOrganizationField(rules, required);
        break;
      case 'S':
        control = this._renderLevel1Field(rules, required);
        break;
      case 'Z':
        control = this._renderPostcodeField(rules, required);
        break;
      }
    return <div className={"col-xs-" + width.toString()} key={controlFormat}>
      {control}
    </div>;
  }
  _renderRow(rowFormat, key, rules) {
    let itemRe = /%([A-Z])/g;
    let results = [];
    let match;
    while (match = itemRe.exec(rowFormat)) {
      if (match[1] !== 'X') {
        // we intentionally skip sorting code as there is no agreement on how to handle it properly
        results.push(match[1]);
      }
    }
    if (results.length === 0) {
      return;
    }
    let width = 12 / results.length;
    let controls = results.map((controlFormat) => this._renderControl(controlFormat, width, rules));
    return <div className="row" key={key}>
      {controls}
    </div>;
  }
  render() {
    let rules = this.getRules();
    let formatString = rules.fmt;
    let formatRows = formatString.split('%n');
    let rows = formatRows.map((formatRow, i) => this._renderRow(formatRow, i, rules));
    return <div>
      {rows}
      <div className="row" key='country'>
        <div className="col-xs-12">
          {this._renderCountryField(rules)}
        </div>
      </div>
    </div>;
  }
};

$(function () {
  let $address = $('.i18n-address');
  let addressUrl = $address.data('address-url');
  $.ajax({
    url: addressUrl,
    dataType: 'json',
    cache: false,
    success: function (data) {
      let countries = [
        'AC', 'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ',
        'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ',
        'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CV', 'CW', 'CX', 'CY', 'CZ',
        'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ',
        'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET',
        'FI', 'FJ', 'FK', 'FM', 'FO', 'FR',
        'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY',
        'HK', 'HM', 'HN', 'HR', 'HT', 'HU',
        'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS',
        'IT', 'JE', 'JM', 'JO', 'JP', 'KE',
        'KG', 'KH', 'KI', 'KM', 'KN', 'KR', 'KW', 'KY', 'KZ',
        'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY',
        'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ',
        'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ',
        'OM',
        'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY',
        'QA',
        'RE', 'RO', 'RS', 'RU', 'RW', 'SA',
        'SB', 'SC', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SZ',
        'TA', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ',
        'UA', 'UG', 'UM', 'US', 'UY', 'UZ',
        'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU',
        'WF', 'WS',
        'XK',
        'YE', 'YT',
        'ZA', 'ZM', 'ZW'
      ];
      ReactDOM.render(
        <AddressForm lang="it" countries={countries} country="CN" data={data} />,
        $address[0]
      );
    }.bind(this),
    error: function (xhr, status, err) {
      console.error(status, err.toString());
    }.bind(this)
  });
});
