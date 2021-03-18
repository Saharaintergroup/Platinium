odoo.define('pos_chque_information.pos', function(require) {
	"use strict";

	var models = require('point_of_sale.models');
	var core = require('web.core');
	const PaymentScreen = require('point_of_sale.PaymentScreen');	
	const { useListener } = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');
	var QWeb = core.qweb;

	var _t = core._t;

	models.load_models({
		model: 'res.bank',
		fields: ['id','name'],
		loaded: function(self, bank){
			self.bank = bank;
		},
	});

	models.load_models({
		model: 'res.partner',
		fields: ['id','name'],
		loaded: function(self, partner){
			self.partner = partner;
		},
	});

	models.load_models({
		model: 'payment.provider',
		fields: ['id','name'],
		loaded: function(self, provider){
			self.provider = provider;
		},
	});

	models.load_models({
		model: 'payment.terminal',
		fields: ['id','name'],
		loaded: function(self, terminal){
			self.terminal = terminal;
		},
	});
	
	models.load_models({
		model:  'pos.payment.method',
		fields: ['name', 'is_cash_count', 'use_payment_terminal', 'cheque_information','require_customer','currency_rate','currency_symbol'],
		domain: function(self, tmp) {
			return [['id', 'in', tmp.payment_method_ids]];
		},
		loaded: function(self, payment_methods) {
			self.payment_methods = payment_methods.sort(function(a,b){
				// prefer cash payment_method to be first in the list
				if (a.is_cash_count && !b.is_cash_count) {
					return -1;
				} else if (!a.is_cash_count && b.is_cash_count) {
					return 1;
				} else {
					return a.id - b.id;
				}
			});
			self.payment_methods_by_id = {};
			_.each(self.payment_methods, function(payment_method) {
				self.payment_methods_by_id[payment_method.id] = payment_method;

				var PaymentInterface = self.electronic_payment_interfaces[payment_method.use_payment_terminal];
				if (PaymentInterface) {
					payment_method.payment_terminal = new PaymentInterface(self, payment_method);
				}
			});
		}
	});

	var posorder_super = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize: function(attr, options) {
			posorder_super.initialize.apply(this,arguments);       
			this.bank_id = this.bank_id || false;
			this.owner_name = this.owner_name || false;
			this.provider_name = this.provider_name || false;
			this.terminal_name = this.terminal_name || false;
//			this.bank_account = this.bank_account || false;
			this.cheque_number = this.cheque_number || false;
		},





		export_as_JSON: function() {
			var json = posorder_super.export_as_JSON.apply(this,arguments);
			json.bank_id = this.bank_id;
			json.owner_name = this.owner_name;
			json.provider_name = this.provider_name;
			json.terminal_name = this.terminal_name;
//			json.bank_account = this.bank_account;
			json.cheque_number = this.cheque_number;

			return json;
		},
		init_from_JSON: function(json) {
			posorder_super.init_from_JSON.apply(this,arguments);
			this.bank_id = json.bank_id;
			this.owner_name = json.owner_name;
			this.provider_name = json.provider_name;
			this.terminal_name = json.terminal_name;
//			this.bank_account = json.bank_account;
			this.cheque_number = json.cheque_number;
		},

		get_bank_name: function() {
			return this.bank_id
		},
		set_bank_name:function(bank_id) {
			this.bank_id = bank_id;
			this.trigger('change');
		},

		get_owner_name:function() {
			return this.owner_name 
		},
		set_owner_name:function(owner_name) {
			this.owner_name = owner_name
			this.trigger('change');
		},

		get_provider_name:function() {
			return this.provider_name
		},
		set_provider_name:function(provider_name) {
			this.provider_name = provider_name
			this.trigger('change');
		},

		get_terminal_name:function() {
			return this.terminal_name
		},
		set_terminal_name:function(terminal_name) {
			this.terminal_name = terminal_name
			this.trigger('change');
		},

//		get_bank_account:function() {
//			return this.bank_account
//		},
//		set_bank_account:function(bank_account) {
//			this.bank_account = bank_account
//			this.trigger('change');
//		},

		get_cheque_number:function() {
			return this.cheque_number 
		},
		set_cheque_number:function(cheque_number) {
			this.cheque_number = cheque_number
			this.trigger('change');
		},

	});

	const PosChequePaymentScreen = (PaymentScreen) =>
		class extends PaymentScreen {
			constructor() {
				super(...arguments);
				useListener('cheque-bank', this.chequeinformation);
			}
			chequeinformation(event) {
				let self = this;
				this.showPopup('ChequeInformationPopup', {
					body: 'Cheque',
					startingValue: self,
					list: self.env.pos.bank,
					list1: self.env.pos.partner,
					list2: self.env.pos.provider,
					list3: self.env.pos.terminal,
                    title: this.env._t('Cheque Information'),
                });
			}
		};

	Registries.Component.extend(PaymentScreen, PosChequePaymentScreen);

	return PosChequePaymentScreen;
});