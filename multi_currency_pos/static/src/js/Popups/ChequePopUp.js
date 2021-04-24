odoo.define('pos_cheque_information.ChequePopup', function(require) {
	"use strict";

	var core = require('web.core');
	const { useState, useRef } = owl.hooks;
	const { useListener } = require('web.custom_hooks');
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
	var QWeb = core.qweb;

	var _t = core._t;

	class ChequeInformationPopup extends AbstractAwaitablePopup {
		constructor() {
			super(...arguments);
			this.inputselectedeRef = useRef('input-selected');
			this.inputNameRef = useRef('input-name');
//			this.inputaccountRef = useRef('input-account');
			this.inputnumberRef = useRef('input-number');
			this.inputproviderRef = useRef('input-provider');
			this.inputterminalRef = useRef('input-terminal');

		}
		mounted() {
            this.inputNameRef.el.focus();
        }

        getValue() {
        	var order = this.env.pos.get_order()
        	if (this.inputnumberRef.el.value == false || this.inputNameRef.el.value == false  || this.inputnumberRef.el.value == false || this.inputproviderRef.el.value == false || this.inputterminalRef.el.value == false){
						this.showPopup('ErrorPopup',{
							'title': _t('Transactions Details'),
							'body': _t('You should Complete Transaction Details.'),
						});
						return false;
					}
        	order.set_bank_name(this.inputselectedeRef.el.value);
			order.set_owner_name(this.inputNameRef.el.value);
//			order.set_bank_account(this.inputaccountRef.el.value);
			order.set_cheque_number(this.inputnumberRef.el.value);
			order.set_provider_name(this.inputproviderRef.el.value);
			order.set_terminal_name(this.inputterminalRef.el.value);

			this.trigger('close-popup');

        }
        cancel() {
        	this.trigger('close-popup');
        }
	}

	ChequeInformationPopup.template = 'ChequeInformationPopup';
	ChequeInformationPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: '',
        body: '',
        list: [],
        startingValue: '',
    };

	Registries.Component.add(ChequeInformationPopup);

	return ChequeInformationPopup;
});