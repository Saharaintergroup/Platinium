odoo.define('point_of_sale.NewPaymentScreenStatus', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');


    var order_model_super = models.Order.prototype;

    models.Order = models.Order.extend({
//        export_for_printing: function () {
//
//            var receipt = order_model_super.export_for_printing.bind(this)();
//            var payment_lines = this.pos.get_order().get_paymentlines()
//
//            for (var i=0; i<payment_lines.length;i++){
//                if (payment_lines[i].payment_method.cheque_information){
//                    receipt = _.extend(receipt, {
//                        second_currency: payment_lines[i].payment_method.currency_rate,
//                         currency_symbol:  payment_lines[i].payment_method.currency_symbol
//                    });
//
//                    return receipt;
//                }
//
//                }
//        }
    export_for_printing: function () {
            var receipt = order_model_super.export_for_printing.bind(this)();
            var payment_lines = this.pos.get_order().get_paymentlines();

            for (var i=0; i<payment_lines.length;i++){
                if (payment_lines[i].payment_method.cheque_information == true ){


                    receipt = _.extend(receipt, {

                        currency_amount : payment_lines[i].payment_method.currency_rate,
                        currency_symbol : payment_lines[i].payment_method.currency_symbol
                    });

                    return receipt;

                }
                else{
                receipt = _.extend(receipt, {

                        currency_amount : 0

                    });

                    return receipt;

                }
                }



        }
    });

    class PaymentScreenStatus extends PosComponent {
        get changeText() {
            return this.env.pos.format_currency(this.currentOrder.get_change());
        }
        get totalDueText() {
            return this.env.pos.format_currency(
                this.currentOrder.get_total_with_tax() + this.currentOrder.get_rounding_applied()
            );
        }
        get remainingText() {
            return this.env.pos.format_currency(
                this.currentOrder.get_due() > 0 ? this.currentOrder.get_due() : 0
            );
        }

            get remainingTextCurrency() {
            var payment_lines = this.env.pos.get_order().get_paymentlines()

            for (var i=0; i<payment_lines.length;i++){
                if (payment_lines[i].payment_method.currency_rate > 0 ){
                    return this.env.pos.format_currency(
                        this.currentOrder.get_due() > 0 ? this.currentOrder.get_due()*payment_lines[i].payment_method.currency_rate : 0
                    );
                }
                else{
                    return;
                    }
                }
        }





        get currentOrder() {
            return this.env.pos.get_order();
        }
    }
    PaymentScreenStatus.template = 'PaymentScreenStatus';

    Registries.Component.add(PaymentScreenStatus);

    return PaymentScreenStatus;
});
