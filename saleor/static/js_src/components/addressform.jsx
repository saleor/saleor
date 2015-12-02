/* @flow */

import React from 'react';
import ReactDOM from 'react-dom';
import {connect} from 'react-redux';
import $ from 'jquery';

type Rules = {fmt: string; require: string};

let FormGroup = ({required, children}) => <div className={required ? "form-group required" : "form-group"}>{children}</div>;

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
    return <FormGroup required={required}>
      <label htmlFor={id} className="control-label">{label}</label>
        <select id={id} name={name} className="form-control" value={value} autoComplete={autoComplete} onChange={onChange} required={required}>
        <option></option>
        {options}
      </select>
    </FormGroup>;
  }
  return <div className={required ? "form-group has-feedback required" : "form-group has-feedback"}>
    <label htmlFor={id} className="control-label">{label}</label>
    <input id={id} name={name} className="form-control" value={value} autoComplete={autoComplete} onChange={onChange} required={required} />
  </div>;
}

let prefixName = (name, prefix) => (prefix ? `${prefix}-${name}` : name);

class AddressForm extends React.Component {
  getRule(parts: Array<string>): {} {
    let rule = {}
    let key = parts.join('/');
    if (key in this.props.data) {
      rule = {...rule, ...this.props.data[key]};
    }
    key = `${key}--${this.props.lang}`;
    if (key in this.props.data) {
      rule = {...rule, ...this.props.data[key]};
    }
    return rule;
  }
  getRules(): Rules {
    let rules = {
      fmt: '%N%n%O%n%A%n%Z %C',
      require: 'AC'
    };
    if (this.props.country) {
      rules = {...rules, ...this.getRule([this.props.country])};
      if (rules.fmt.indexOf('%S') !== -1) {
        if (this.props.level1) {
          rules = {...rules, ...this.getRule([this.props.country, this.props.level1])};
          if (rules.fmt.indexOf('%C') !== -1) {
            if (this.props.level2) {
              rules = {...rules, ...this.getRule([this.props.country, this.props.level1, this.props.level2])};
            }
          }
        }
      } else {
        if (rules.fmt.indexOf('%C') !== -1) {
          if (this.props.level2) {
            rules = {...rules, ...this.getRule([this.props.country, this.props.level2])};
          }
        }
      }
    }
    return rules;
  }
  _renderAddressField(rules: Rules, required: boolean, prefix: string): React.Component {
    return <div className="row">
      <div className="col-xs-8">
        <FormGroup required={required}>
          <label htmlFor="field-address1" className="control-label">Address</label>
          <input id="field-address1" className="form-control" name={prefixName('street_address_1', prefix)} autoComplete="address-line1" required={required} onChange={this._onAddress1Change.bind(this)} value={this.props.address1} />
        </FormGroup>
      </div>
      <div className="col-xs-4">
        <FormGroup required={false}>
          <label htmlFor="field-address2" className="control-label">Address</label>
          <input id="field-address2" className="form-control" name={prefixName('street_address_2', prefix)} autoComplete="address-line2" onChange={this._onAddress2Change.bind(this)} value={this.props.address2} />
        </FormGroup>
      </div>
    </div>;
  }
  _renderCountryField(rules: Rules, prefix: string): React.Component {
    let options = this.props.countries.map((code) => {
      let countryRules = this.getRule([code]);
      let name = code;
      if (countryRules.hasOwnProperty('name')) {
        name = countryRules.name;
      }
      return <option value={code} key={code}>{name}</option>;
    });
    return <FormGroup required={true}>
      <label htmlFor="field-country" className="control-label">Country/region</label>
      <select id="field-country" name={prefixName('country', prefix)} className="form-control" value={this.props.country} autoComplete="country" ref="country" onChange={this._onCountryChange.bind(this)} required={true}>
        {options}
      </select>
    </FormGroup>;
  }
  _renderLevel1Field(rules: Rules, required: boolean, prefix: string) {
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
      };
      label = map[rules.state_name_type];
    }
    let countryRules = {};
    if (this.props.country) {
      let nodes = [this.props.country];
      countryRules = this.getRule(nodes);
    }
    return <LevelSelect rules={countryRules} id="field-level1" name={prefixName('country_area', prefix)} autoComplete="address-level1" onChange={this._onLevel1Change.bind(this)} label={label} value={this.props.level1} required={required} />;
  }
  _renderLevel2Field(rules: Rules, required: boolean, prefix: string) {
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
      if (this.props.country && this.props.level1) {
        let nodes = [this.props.country, this.props.level1];
        levelRules = this.getRule(nodes);
      }
    } else if (this.props.country) {
      let nodes = [this.props.country];
      levelRules = this.getRule(nodes);
    }
    return <LevelSelect rules={levelRules} id="field-level2" name={prefixName('city', prefix)} autoComplete="address-level2" onChange={this._onLevel2Change.bind(this)} label={label} value={this.props.level2} required={required} />;
  }
  _renderLevel3Field(rules: Rules, required: boolean, prefix: string) {
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
      if (this.props.country && this.props.level1 && this.props.level2) {
        let nodes = [this.props.country, this.props.level1, this.props.level2];
        levelRules = this.getRule(nodes);
      }
    } else {
      if (this.props.country && this.props.level2) {
        let nodes = [this.props.country, this.props.level2];
        levelRules = this.getRule(nodes);
      }
    }
    return <LevelSelect rules={levelRules} id="field-level3" name={prefixName('country_area_2', prefix)} autoComplete="address-level3" onChange={this._onLevel3Change.bind(this)} label={label} value={this.props.level3} required={required} />;
  }
  _renderNameField(rules: Rules, required: boolean, prefix: string): React.Component {
    return <div className="row">
      <div className="col-xs-6">
        <FormGroup required={required}>
          <label htmlFor="field-country" className="control-label">First name</label>
          <input className="form-control" name={prefixName('first_name', prefix)} autoComplete="given-name" required={required} onChange={this._onFirstNameChange.bind(this)} value={this.props.firstName} />
        </FormGroup>
      </div>
      <div className="col-xs-6">
        <FormGroup required={required}>
          <label htmlFor="field-country" className="control-label">Last name</label>
          <input className="form-control" name={prefixName('last_name', prefix)} autoComplete="family-name" required={required} onChange={this._onLastNameChange.bind(this)} value={this.props.lastName} />
        </FormGroup>
      </div>
    </div>;
  }
  _renderOrganizationField(rules: Rules, required: boolean, prefix: string): React.Component {
    return <FormGroup required={required}>
      <label htmlFor="field-country" className="control-label">Company/organization</label>
      <input className="form-control" name={prefixName('company_name', prefix)} autoComplete="organization" required={required} onChange={this._onOrganizationChange.bind(this)} value={this.props.organization} />
    </FormGroup>;
  }
  _renderPostcodeField(rules: Rules, required: boolean, prefix: string): React.Component {
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
      return <FormGroup required={required}>
        <label htmlFor="field-postcode" className="control-label">{label}</label>
        <div className="input-group">
          <div className="input-group-addon">{rules.postprefix}</div>
          <input type="text" className="form-control" name={prefixName('postal_code', prefix)} autoComplete="postal-code" required={required} pattern={pattern} onChange={this._onPostcodeChange.bind(this)} value={this.props.postcode} />
        </div>
        {hint ? <span className="help-block">{hint}</span> : undefined}
      </FormGroup>;
    }
    return <FormGroup required={required}>
      <label htmlFor="field-postcode" className="control-label">{label}</label>
      <input type="text" className="form-control" name={prefixName('postal_code', prefix)} autoComplete="postal-code" required={required} pattern={pattern} onChange={this._onPostcodeChange.bind(this)} value={this.props.postcode} />
      {hint ? <span className="help-block">{hint}</span> : undefined}
    </FormGroup>;
  }
  _onCountryChange(event: React.event) {
    let country = event.target.value;
    this.props.dispatch({type: 'SET_COUNTRY', country});
  }
  _onLevel1Change(event: React.event) {
    let level1 = event.target.value;
    this.props.dispatch({type: 'SET_LEVEL1', level1});
  }
  _onLevel2Change(event: React.event) {
    let level2 = event.target.value;
    this.props.dispatch({type: 'SET_LEVEL2', level2});
  }
  _onLevel3Change(event: React.event) {
    let level3 = event.target.value;
    this.props.dispatch({type: 'SET_LEVEL3', level3});
  }
  _onFirstNameChange(event: React.event) {
    let firstName = event.target.value;
    this.props.dispatch({type: 'SET_FIRST_NAME', firstName});
  }
  _onLastNameChange(event: React.event) {
    let lastName = event.target.value;
    this.props.dispatch({type: 'SET_LAST_NAME', lastName});
  }
  _onOrganizationChange(event: React.event) {
    let organization = event.target.value;
    this.props.dispatch({type: 'SET_ORGANIZATION', organization});
  }
  _onPostcodeChange(event: React.event) {
    let postcode = event.target.value;
    this.props.dispatch({type: 'SET_POSTCODE', postcode});
  }
  _onAddress1Change(event: React.event) {
    let address1 = event.target.value;
    this.props.dispatch({type: 'SET_ADDRESS1', address1});
  }
  _onAddress2Change(event: React.event) {
    let address2 = event.target.value;
    this.props.dispatch({type: 'SET_ADDRESS2', address2});
  }
  _renderControl(controlFormat: string, width: number, rules: Rules): React.Component {
    let control;
    let required = rules.require.indexOf(controlFormat) !== -1;
    let prefix = this.props.prefix;
    switch (controlFormat) {
      case 'A':
        control = this._renderAddressField(rules, required, prefix);
        break;
      case 'C':
        control = this._renderLevel2Field(rules, required, prefix);
        break;
      case 'D':
        control = this._renderLevel3Field(rules, required, prefix);
        break;
      case 'N':
        control = this._renderNameField(rules, true, prefix);
        break;
      case 'O':
        control = this._renderOrganizationField(rules, required, prefix);
        break;
      case 'S':
        control = this._renderLevel1Field(rules, required, prefix);
        break;
      case 'Z':
        control = this._renderPostcodeField(rules, required, prefix);
        break;
      }
    return <div className={"col-xs-" + width.toString()} key={controlFormat}>
      {control}
    </div>;
  }
  _renderRow(rowFormat: string, key: string, rules: Rules) {
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
  render(): React.Component {
    let rules = this.getRules();
    let formatString = rules.fmt;
    let formatRows = formatString.split('%n');
    let rows = formatRows.map((formatRow, i) => this._renderRow(formatRow, i.toString(), rules));
    let prefix = this.props.prefix;
    return <div>
      {rows}
      <div className="row" key='country'>
        <div className="col-xs-12">
          {this._renderCountryField(rules, prefix)}
        </div>
      </div>
    </div>;
  }
};

function select(state) {
  return state;
}

export default connect(select)(AddressForm);
